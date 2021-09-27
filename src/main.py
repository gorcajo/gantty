import argparse
import curses
import signal
import sys
import time
import traceback
import yaml


FRAME_RATE = 60
MARGIN = 2


class Gantty:

    def __init__(self, file_path: str) -> None:
        project = yaml.safe_load(open(file_path, 'r'))

        self.resources = {resource['name']: Resource(resource['name']) for resource in project['resources']}
        self.tasks = [Task(task['name'], task['id'], task['duration'], task['depends_on'], task['done'], task['asignee']) for task in project['tasks']]

        self.check_project()
        self.calculate_bars()

        self.running = False
        self.screen = None


    def check_project(self) -> None:
        task_ids = [task.id for task in self.tasks]

        if len(task_ids) != len(list(set(task_ids))):
            raise ValueError(f'There are tasks with duplicater IDs')

        for task in self.tasks:
            if task.asignee not in self.resources:
                raise ValueError(f'Asignee "{task.asignee}" in task with ID "{task.id}" not found in resources')


    def calculate_bars(self) -> None:
        for resource in self.resources.values():
            resource.unschedule_all_bars()

        prev_task = None

        for task in self.tasks:
            resource = self.resources[task.asignee]

            if task.depends_on is None:
                task.bar = resource.scheduled_bars * ' ' + task.duration * '#'
                resource.schedule_bars(task.duration)

            elif task.depends_on == -1:
                if prev_task is not None:
                    task.bar = len(prev_task.bar) * ' ' + task.duration * '#'
                else:
                    task.bar = task.duration * '#'

                resource.schedule_bars(task.duration)

            elif task.depends_on > 0:
                raise NotImplementedError()

            prev_task = task


    def loop(self) -> None:
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)

        self.running = True

        while self.running:
            try:
                self.draw()
                self.screen.refresh()
                time.sleep(1 / FRAME_RATE)
            except:
                self.exit()
                print(traceback.format_exc())


    def draw(self) -> None:
        longest_task_id = max([len(str(task.id)) for task in self.tasks])
        longest_task_name = max([len(task.name) for task in self.tasks])
        longest_asignee_name = max([len(task.asignee) for task in self.tasks])

        x_offset = 0
        self.screen.addstr(0, x_offset, 'ID')

        x_offset += longest_task_id + MARGIN
        self.screen.addstr(0, x_offset, 'TASK NAME')

        x_offset += longest_task_name + MARGIN
        self.screen.addstr(0, x_offset, 'ASIGNEE')

        for i, task in enumerate(self.tasks):
            x_offset = 0
            self.screen.addstr(i + 1, x_offset, str(task.id))

            x_offset += longest_task_id + MARGIN
            self.screen.addstr(i + 1, x_offset, task.name)

            x_offset += longest_task_name + MARGIN
            self.screen.addstr(i + 1, x_offset, task.asignee)

            x_offset += longest_asignee_name + MARGIN
            self.screen.addstr(i + 1, x_offset, task.bar)


    def exit(self, sig: int = None, frame = None) -> None:
        curses.nocbreak()
        self.screen.keypad(False)
        curses.echo()
        curses.endwin()
        self.running = False


class Resource:

    def __init__(self, name: str) -> None:
        self._name = name
        self._scheduled_bars = 0


    def schedule_bars(self, bars: int) -> None:
        self._scheduled_bars += bars


    def unschedule_all_bars(self) -> None:
        self._scheduled_bars = 0


    @property
    def name(self) -> str:
        return self._name


    @property
    def scheduled_bars(self) -> int:
        return self._scheduled_bars


    def __str__(self) -> str:
        return f'Resource(name={self.name})'


    def __repr__(self) -> str:
        return self.__str__()


class Task:

    def __init__(self, name: str, task_id: int, duration: int, depends_on: int, done: int, asignee: str) -> None:
        self._name = name
        self._id = task_id
        self._duration = duration
        self._depends_on = depends_on
        self._done = done
        self._asignee = asignee
        self._bar = ''


    @property
    def name(self) -> str:
        return self._name


    @property
    def id(self) -> int:
        return self._id


    @property
    def duration(self) -> int:
        return self._duration


    @property
    def depends_on(self) -> int:
        return self._depends_on


    @property
    def asignee(self) -> str:
        return self._asignee


    @property
    def bar(self) -> str:
        return self._bar


    @bar.setter
    def bar(self, new_bar: str) -> None:
        self._bar = new_bar


    def __str__(self) -> str:
        return f'Task(id={self.id})'


    def __repr__(self) -> str:
        return self.__str__()


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str, required=True, help='project file')
    args = parser.parse_args()

    gantty = Gantty(args.file)
    signal.signal(signal.SIGINT, gantty.exit)
    gantty.loop()
