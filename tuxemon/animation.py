# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from enum import Enum
from math import cos, pi, sin, sqrt
from typing import Any, Optional, Union

from pygame.sprite import Group, Sprite

__all__ = ("Task", "Animation", "remove_animations_of")

from tuxemon.compat import Rect

ScheduledFunction = Callable[[], Any]

logger = logging.getLogger(__name__)


class AnimationState(Enum):
    NOT_STARTED = 0
    RUNNING = 1
    DELAYED = 2
    FINISHED = 3


class ScheduleType(Enum):
    ON_UPDATE = "on update"
    ON_FINISH = "on finish"
    ON_ABORT = "on abort"
    ON_INTERVAL = "on interval"


def check_number(value: Any) -> float:
    """
    Test if an object is a number.

    Raises ``ValueError`` when ``value`` is not a number.

    Parameters:
        value: Some object.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError


def remove_animations_of(
    target: object, group: Group[Union[Task, Animation]]
) -> None:
    """
    Removes animations associated with a given target.

    Parameters:
        target: The object whose animations should be removed.
        group: A Pygame group containing `Animation` instances.
    """
    animations = {ani for ani in group if isinstance(ani, Animation)}
    to_remove = [
        ani for ani in animations if target in [i[0] for i in ani.targets]
    ]
    if not to_remove:
        logger.debug(f"No animations found for target: {target}")
    group.remove(*to_remove)


class TaskBase(Sprite):
    _valid_schedules: Sequence[ScheduleType] = []

    def __init__(self) -> None:
        super().__init__()
        self._callbacks: defaultdict[
            ScheduleType,
            list[tuple[ScheduledFunction, tuple[Any, ...], dict[str, Any]]],
        ] = defaultdict(list)

    def schedule(
        self,
        func: ScheduledFunction,
        when: Optional[ScheduleType] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Schedule a callback during operation of Task or Animation.

        The callback is any callable object.  You can specify different
        times for the callback to be executed, according to the following:

        * "on update": called each time the Task/Animation is updated.
        * "on finish": called when the Task/Animation completes normally.
        * "on abort": called if the Task/Animation is aborted.
        * "on interval": called each interval for Tasks.

        If when is not passed, it will be the first valid schedule type.

        Parameters:
            func: Callable to schedule.
            when: Time when ``func`` is going to be called.
            args: Positional arguments to pass to the callback.
            kwargs: Keyword arguments to pass to the callback.
        """
        if when is None:
            when = self._valid_schedules[0]

        if when not in self._valid_schedules:
            raise ValueError(
                f"Invalid time to schedule a callback: '{when.value}'. "
                f"Valid options: {[s.value for s in self._valid_schedules]}"
            )

        self._callbacks[when].append((func, args, kwargs))

    def _execute_callbacks(self, when: ScheduleType) -> None:
        """
        Execute all scheduled callbacks for a given time.
        """
        if when in self._callbacks:
            for func, args, kwargs in self._callbacks[when]:
                func(*args, **kwargs)


class Task(TaskBase):
    """
    Execute functions at a later time and optionally loop it.

    This is a silly little class meant to make it easy to create
    delayed or looping events without any complicated hooks into
    pygame's clock or event loop.

    Tasks are created and must be added to a normal pygame group
    in order to function.  This group must be updated, but not
    drawn.

    Setting the interval to 0 cause the callback to be called
    on the next update.

    Because the pygame clock returns milliseconds, the examples
    below use milliseconds.  However, you are free to use whatever
    time unit you wish, as long as it is used consistently.

    Parameters:
        callback: Function to execute each interval.
        interval: Time between callbacks.
        times: Number of intervals.

    Examples:
        >>> task_group = Group()

        >>> # like a delay
        >>> def call_later():
        ...    pass
        >>> task = Task(call_later, 1000)
        >>> task_group.add(task)

        >>> # do something 24 times at 1 second intervals
        >>> task = Task(call_later, 1000, 24)

        >>> # do something every 2.5 seconds forever
        >>> task = Task(call_later, 2500, -1)

        >>> # pass arguments using functools.partial
        >>> from functools import partial
        >>> task = Task(partial(call_later(1,2,3, key=value)), 1000)

        >>> # a task must have at lease on callback, but others can be added
        >>> task = Task(call_later, 2500, -1)
        >>> task.schedule(some_thing_else)

        >>> # chain tasks: when one task finishes, start another one
        >>> task = Task(call_later, 2500)
        >>> task.chain(Task(something_else))

        When chaining tasks, do not add the chained tasks to a group.
    """

    _valid_schedules = (
        ScheduleType.ON_INTERVAL,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(
        self,
        callback: ScheduledFunction,
        interval: float = 0,
        times: int = 1,
    ) -> None:
        if not callable(callback):
            raise ValueError("callback must be callable")

        if interval < 0:
            raise ValueError("interval must be non negative")

        if times < -1 or times == 0:
            raise ValueError(
                "times must be -1 for infinite loops, or a positive integer (>= 1)"
            )

        super().__init__()
        self._interval = interval
        self._loops = times
        self._duration: float = 0
        self._chain: list[Task] = []
        self._state = AnimationState.RUNNING
        self.schedule(callback, ScheduleType.ON_INTERVAL)

    def chain(
        self,
        callback: ScheduledFunction,
        interval: float = 0,
        times: int = 1,
    ) -> None:
        """
        Schedule a callback to execute when this one is finished

        If you attempt to chain a task to a task that will
        never end, RuntimeError will be raised.

        This is convenience to make a new Task and set to it to
        be added to the "on_finish" list.

        Parameters:
            callback: Function to execute each interval.
            interval: Time between callbacks.
            times: Number of intervals.
        """
        self.chain_task(Task(callback, interval, times))

    def chain_task(self, *others: Task) -> Sequence[Task]:
        """
        Schedule Task(s) to execute when this one is finished.

        If you attempt to chain a task to a task that will
        never end, RuntimeError will be raised.

        Parameters:
            others: Task instances.

        Returns:
            The sequence of added Tasks.
        """
        if self._loops == -1:
            raise RuntimeError("Cannot chain a task to an infinite loop task.")
        for task in others:
            if not isinstance(task, Task):
                raise TypeError(f"Expected Task, got {type(task).__name__}")
            self._chain.append(task)
        return others

    def update(self, dt: float) -> None:
        """
        Update the Task.

        The unit of time passed must match the one used in the
        constructor.

        Task will not 'make up for lost time'. If an interval
        was skipped because of a lagging clock, then callbacks
        will not be made to account for the missed ones.

        Parameters:
            dt: Time passed since last update.
        """
        if self._state is not AnimationState.RUNNING:
            raise RuntimeError(
                f"Task cannot proceed: expected state "
                f" {AnimationState.RUNNING.name}, but found {self._state.name}."
            )

        self._duration += dt
        self._execute_callbacks(ScheduleType.ON_UPDATE)
        if self._duration >= self._interval:
            self._duration -= self._interval
            if self._loops > 0:
                self._loops -= 1
                if self._loops == 0:
                    self.finish()
                else:
                    self._execute_callbacks(ScheduleType.ON_INTERVAL)
            elif self._loops == -1:
                self._execute_callbacks(ScheduleType.ON_INTERVAL)

    def finish(self) -> None:
        """Force task to finish, while executing callbacks."""
        if self._state is AnimationState.RUNNING:
            self._state = AnimationState.FINISHED
            self._execute_callbacks(ScheduleType.ON_INTERVAL)
            self._execute_callbacks(ScheduleType.ON_FINISH)
            self._execute_chain()
            self._cleanup()
        else:
            logger.debug(
                "Task already finished or not running, cannot finish again."
            )

    def is_finish(self) -> bool:
        """
        Returns:
            Whether the task is finished or not.
        """
        return self._state is AnimationState.FINISHED

    def reset_delay(self, new_delay: float) -> None:
        """
        Reset the delay before starting task to make sure time left is
        equal or bigger to the provided value

        Parameters:
            new_delay: the updated delay that should be respected
        """
        time_left = self._interval - self._duration
        if new_delay > time_left:
            self._interval = new_delay
            self._duration = 0

    def abort(self) -> None:
        """Force task to finish, without executing 'on interval' callbacks."""
        if self._state is AnimationState.FINISHED:
            return

        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self._cleanup()

    def _cleanup(self) -> None:
        self._chain = []
        self.kill()

    def _execute_chain(self) -> None:
        groups = self.groups()
        for task in self._chain:
            task.add(*groups)


class Animation(Sprite):
    """
    Change numeric values over time.

    To animate a target sprite/object's position, simply specify
    the target x/y values where you want the widget positioned at
    the end of the animation.  Then call start while passing the
    target as the only parameter.

        >>> ani = Animation(x=100, y=100, duration=1000)
        >>> ani.start(sprite)

    The shorthand method of starting animations is to pass the
    targets as positional arguments in the constructor.

        >>> ani = Animation(sprite.rect, x=100, y=0)

    If you would rather specify relative values, then pass the
    relative keyword and the values will be adjusted for you:

        >>> ani = Animation(x=100, y=100, duration=1000)
        >>> ani.start(sprite, relative=True)

    You can also specify a callback that will be executed when the
    animation finishes:

        >>> ani.schedule(my_function)

    Another optional callback is available that is called after
    each update:

        >>> ani.update_callback = post_update_function

    Animations must be added to a sprite group in order for them
    to be updated.  If the sprite group that contains them is
    drawn then an exception will be raised, so you should create
    a sprite group only for containing Animations.

    You can cancel the animation by calling ``Animation.abort()``.

    When the animation has finished, then it will remove itself
    from the sprite group that contains it.

    You can optionally delay the start of the animation using the
    delay keyword.


    **Callable Attributes**

    Target values can also be callable.  In this case, there is
    no way to determine the initial value unless it is specified
    in the constructor.  If no initial value is specified, it will
    default to 0.

    Like target arguments, the initial value can also refer to a
    callable.

    NOTE: Specifying an initial value will set the initial value
          for all target names in the constructor.  This
          limitation won't be resolved for a while.


    **Pygame Rects**

    The 'round_values' parameter will be set to True automatically
    if pygame rects are used as an animation target.

    Parameters:
        targets: Any valid python objects.
        delay: Delay time before the animation starts.
        round_values: Wether the values must be rounded to the nearest
            integer before being set.
        duration: Time duration of the animation.
        transition: Transition to use in the animation. Can be the name
            of a method of :class:`AnimationTransition` or a callable
            with the same signature.
        initial: Initial value. Can be numeric or a callable that
            returns a numeric value. If ``None`` the value itself is used.
        relative: If the values are relative to the initial value. That is,
            in order to find the actual value one has to add the initial
            one.
        kwargs: Properties of the ``targets`` to be used, and their values.
    """

    default_duration = 1000.0
    default_transition = "linear"

    def __init__(
        self,
        *targets: object,
        delay: float = 0,
        round_values: bool = False,
        duration: Optional[float] = None,
        transition: Union[str, Callable[[float], float], None] = None,
        initial: Union[float, Callable[[], float], None] = None,
        relative: bool = False,
        callback: Optional[ScheduledFunction] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.callback = callback
        self.update_callback: ScheduledFunction

        self.targets: list[
            tuple[object, Mapping[str, tuple[float, float]]]
        ] = list()
        self._targets: Sequence[object] = list()
        self.delay = delay
        self._state = AnimationState.NOT_STARTED
        self._round_values = round_values

        self._duration = (
            self.default_duration if duration is None else duration
        )

        self._transition = self._resolve_transition(transition)
        self._initial = initial
        self._relative = relative
        self._elapsed = 0.0

        if not kwargs:
            raise ValueError(
                "Animation must have at least one property to modify"
            )
        self.props = kwargs

        if targets:
            self.start(*targets)

    def schedule(
        self, func: ScheduledFunction, when: str = "on finish"
    ) -> None:
        if when != "on finish":
            raise ValueError("Animation only supports 'on finish' scheduling.")
        logger.debug(f"Scheduled animation callback for {self} at '{when}'.")
        self.callback = func

    def _resolve_transition(
        self, transition: Union[str, Callable[[float], float], None] = None
    ) -> Callable[[float], float]:
        if transition is None:
            transition = self.default_transition

        if isinstance(transition, str):
            transition = getattr(AnimationTransition, transition)
            if not callable(transition):
                raise ValueError(f"Invalid transition name: {transition}")

        if not callable(transition):
            raise TypeError(
                "Provided transition must be a callable function or a valid string identifier"
            )

        return transition

    def _get_value(self, target: object, name: str) -> float:
        """
        Get value of an attribute, even if it is a callable.

        Parameters:
            target: Object that contains the attribute.
            name: Name of the attribute to get the value from.

        Returns:
            Attribute value.
        """
        if self._initial is None:
            value = getattr(target, name)
        else:
            value = self._initial

        if callable(value):
            value = value()

        return check_number(value)

    def _set_value(self, target: object, name: str, value: float) -> None:
        """
        Set a value on some other object.

        If the name references a callable type, then
        the object of that name will be called with 'value'
        as the first and only argument.

        Because callables are 'write only', there is no way
        to determine the initial value.  you can supply
        an initial value in the constructor as a value or
        reference to a callable object.

        Parameters:
            target: Object to be modified.
            name: Name of attribute to be modified.
            value: New value of the attribute.
        """
        if self._round_values:
            value = round(value)

        attr = getattr(target, name)
        if callable(attr):
            attr(value)
        else:
            setattr(target, name, value)

    def update(self, dt: float) -> None:
        """
        Update the animation.

        The unit of time passed must match the one used in the
        constructor.

        Make sure that you start the animation, otherwise your
        animation will not be changed during update().

        Will raise RuntimeError if animation is updated after
        it has finished.

        Parameters:
            dt: Time passed since last update.
        """
        if self._state is AnimationState.FINISHED:
            return
            # raise RuntimeError

        if self._state is not AnimationState.RUNNING:
            return

        self._elapsed += dt
        if self.delay > 0:
            if self._elapsed > self.delay:
                self._elapsed -= self.delay
                self._gather_initial_values()
                self.delay = 0
            return

        p = min(1.0, self._elapsed / self._duration)
        t = self._transition(p)
        for target, props in self.targets:
            for name, values in props.items():
                a, b = values
                value = (a * (1.0 - t)) + (b * t)
                self._set_value(target, name, value)

        if hasattr(self, "update_callback"):
            self.update_callback()

        if p >= 1:
            self.finish()

    def finish(self) -> None:
        """
        Force animation to finish, apply transforms, and execute callbacks.

        * Update callback will be called because the value is changed.
        * Final callback ('callback') will be called.
        * Final values will be applied.
        * Animation will be removed from group.
        """
        # if self._state is not AnimationState.RUNNING:
        #     raise RuntimeError

        if self.targets is not None:
            for target, props in self.targets:
                for name, values in props.items():
                    a, b = values
                    self._set_value(target, name, b)

        if hasattr(self, "update_callback"):
            self.update_callback()

        self.abort()

    def abort(self) -> None:
        """
        Force animation to finish, without any cleanup.

        * Update callback will not be executed.
        * Final callback will be executed.
        * Values will not change.
        * Animation will be removed from group.
        """
        # if self._state is not AnimationState.RUNNING:
        #     raise RuntimeError

        if self._state is AnimationState.FINISHED:
            logger.debug("Animation already finished; abort skipped.")
            return

        self._state = AnimationState.FINISHED
        self.targets = []
        self.kill()
        if self.callback:
            logger.debug("Animation callback triggered on abort.")
            self.callback()

    def start(self, *targets: object, **kwargs: Any) -> None:
        """
        Start the animation on a target sprite/object.

        Targets must have the attributes that were set when
        this animation was created.

        Parameters:
            targets: Any valid python objects.
            kwargs: Ignored.

        Raises:
            RuntimeError: If the animation is already started.
        """
        # TODO: weakref the targets
        if self._state is not AnimationState.NOT_STARTED:
            raise RuntimeError

        self._state = AnimationState.RUNNING
        self._targets = targets

        if self.delay == 0:
            self._gather_initial_values()

    def _gather_initial_values(self) -> None:
        self.targets = list()
        for target in self._targets:
            props = dict()
            if isinstance(target, Rect):
                self._round_values = True
            for name, value in self.props.items():
                initial = self._get_value(target, name)
                check_number(initial)
                check_number(value)
                if self._relative:
                    value += initial
                props[name] = initial, value
            self.targets.append((target, props))

        self.update(0)


class AnimationTransition:
    """
    Collection of animation functions to be used with the Animation object.

    Easing Functions ported to Kivy from the Clutter Project
    http://www.clutter-project.org/docs/clutter/stable/ClutterAlpha.html

    The `progress` parameter in each animation function is in the range 0-1.
    """

    @staticmethod
    def linear(progress: float) -> float:
        return progress

    @staticmethod
    def in_quad(progress: float) -> float:
        return progress * progress

    @staticmethod
    def out_quad(progress: float) -> float:
        return -1.0 * progress * (progress - 2.0)

    @staticmethod
    def in_out_quad(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p
        p -= 1.0
        return -0.5 * (p * (p - 2.0) - 1.0)

    @staticmethod
    def in_cubic(progress: float) -> float:
        return progress * progress * progress

    @staticmethod
    def out_cubic(progress: float) -> float:
        p = progress - 1.0
        return p * p * p + 1.0

    @staticmethod
    def in_out_cubic(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p
        p -= 2
        return 0.5 * (p * p * p + 2.0)

    @staticmethod
    def in_quart(progress: float) -> float:
        return progress * progress * progress * progress

    @staticmethod
    def out_quart(progress: float) -> float:
        p = progress - 1.0
        return -1.0 * (p * p * p * p - 1.0)

    @staticmethod
    def in_out_quart(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p
        p -= 2
        return -0.5 * (p * p * p * p - 2.0)

    @staticmethod
    def in_quint(progress: float) -> float:
        return progress * progress * progress * progress * progress

    @staticmethod
    def out_quint(progress: float) -> float:
        p = progress - 1.0
        return p * p * p * p * p + 1.0

    @staticmethod
    def in_out_quint(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p * p
        p -= 2.0
        return 0.5 * (p * p * p * p * p + 2.0)

    @staticmethod
    def in_sine(progress: float) -> float:
        return -1.0 * cos(progress * (pi / 2.0)) + 1.0

    @staticmethod
    def out_sine(progress: float) -> float:
        return sin(progress * (pi / 2.0))

    @staticmethod
    def in_out_sine(progress: float) -> float:
        return -0.5 * (cos(pi * progress) - 1.0)

    @staticmethod
    def in_expo(progress: float) -> float:
        if progress == 0:
            return 0.0
        value = pow(2, 10 * (progress - 1.0))
        return float(value)

    @staticmethod
    def out_expo(progress: float) -> float:
        if progress == 1.0:
            return 1.0
        value = -pow(2, -10 * progress) + 1.0
        return float(value)

    @staticmethod
    def in_out_expo(progress: float) -> float:
        if progress == 0:
            return 0.0
        if progress == 1.0:
            return 1.0
        p = progress * 2
        if p < 1:
            value = 0.5 * pow(2, 10 * (p - 1.0))
            return float(value)
        p -= 1.0
        value = 0.5 * (-pow(2, -10 * p) + 2.0)
        return float(value)

    @staticmethod
    def in_circ(progress: float) -> float:
        return -1.0 * (sqrt(1.0 - progress * progress) - 1.0)

    @staticmethod
    def out_circ(progress: float) -> float:
        p = progress - 1.0
        return sqrt(1.0 - p * p)

    @staticmethod
    def in_out_circ(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return -0.5 * (sqrt(1.0 - p * p) - 1.0)
        p -= 2.0
        return 0.5 * (sqrt(1.0 - p * p) + 1.0)

    @staticmethod
    def in_elastic(progress: float) -> float:
        p = 0.3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        q -= 1.0
        value = -(pow(2, 10 * q) * sin((q - s) * (2 * pi) / p))
        return float(value)

    @staticmethod
    def out_elastic(progress: float) -> float:
        p = 0.3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        value = pow(2, -10 * q) * sin((q - s) * (2 * pi) / p) + 1.0
        return float(value)

    @staticmethod
    def in_out_elastic(progress: float) -> float:
        p = 0.3 * 1.5
        s = p / 4.0
        q = progress * 2
        if q == 2:
            return 1.0
        if q < 1:
            q -= 1.0
            value = -0.5 * (pow(2, 10 * q) * sin((q - s) * (2.0 * pi) / p))
            return float(value)
        else:
            q -= 1.0
            value = pow(2, -10 * q) * sin((q - s) * (2.0 * pi) / p) * 0.5 + 1.0
            return float(value)

    @staticmethod
    def in_back(progress: float) -> float:
        return progress * progress * ((1.70158 + 1.0) * progress - 1.70158)

    @staticmethod
    def out_back(progress: float) -> float:
        p = progress - 1.0
        return p * p * ((1.70158 + 1) * p + 1.70158) + 1.0

    @staticmethod
    def in_out_back(progress: float) -> float:
        p = progress * 2.0
        s = 1.70158 * 1.525
        if p < 1:
            return 0.5 * (p * p * ((s + 1.0) * p - s))
        p -= 2.0
        return 0.5 * (p * p * ((s + 1.0) * p + s) + 2.0)

    @staticmethod
    def _out_bounce_internal(t: float, d: float) -> float:
        p = t / d
        if p < (1.0 / 2.75):
            return 7.5625 * p * p
        elif p < (2.0 / 2.75):
            p -= 1.5 / 2.75
            return 7.5625 * p * p + 0.75
        elif p < (2.5 / 2.75):
            p -= 2.25 / 2.75
            return 7.5625 * p * p + 0.9375
        else:
            p -= 2.625 / 2.75
            return 7.5625 * p * p + 0.984375

    @staticmethod
    def _in_bounce_internal(t: float, d: float) -> float:
        return 1.0 - AnimationTransition._out_bounce_internal(d - t, d)

    @staticmethod
    def in_bounce(progress: float) -> float:
        return AnimationTransition._in_bounce_internal(progress, 1.0)

    @staticmethod
    def out_bounce(progress: float) -> float:
        return AnimationTransition._out_bounce_internal(progress, 1.0)

    @staticmethod
    def in_out_bounce(progress: float) -> float:
        p = progress * 2.0
        if p < 1.0:
            return AnimationTransition._in_bounce_internal(p, 1.0) * 0.5
        return (
            AnimationTransition._out_bounce_internal(p - 1.0, 1.0) * 0.5 + 0.5
        )
