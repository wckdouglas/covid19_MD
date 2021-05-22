import os
from datetime import date, timedelta
import subprocess
import shlex
import logging

import luigi
from luigi.mock import MockTarget

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s || %(levelname)s  || %(name)s || %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Update")

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.dirname(WORKING_DIR) + "/wckdouglas.github.io"
FIRST_DAY = date(2020, 4, 12)
TODAY = date.today()


class GetData(luigi.Task):
    '''
    For a given date (e.g. "2021-05-01"), retrieve data and save it to data/
    '''
    day = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(WORKING_DIR + "/data/{}.tsv".format(self.day))

    def run(self):  # work if SGE
        cmd = "python dashboard.py get --date {}".format(self.day)
        logger.debug("Getting {}".format(self.output().path))
        with self.output().open("w") as out:
            subprocess.run(shlex.split(cmd), stdout=out)


class SyncRepo(luigi.Task):
    """
    1. git pull
    2. git add the newly added file in data/
    3. git push 
    """
    def output(self):
        return MockTarget("git_dashboard", mirror_on_stderr=True)

    def requires(self):
        return [GetData(day=str(day)) for day in date_range(FIRST_DAY, TODAY)]

    def run(self):
        subprocess.call(["git", "pull"])
        for task in self.requires():
            subprocess.call(shlex.split("git add {}".format(task.output().path)))
            logger.debug("Added {}".format(task.output().path))
        subprocess.call(["git", "push"])
        with self.output().open("w") as out:
            print("git_pull", file=out)


class UpdateDashboard(luigi.Task):
    """
    refresh the dash board 

    :param force (bool): remove the existing dashboard.html and rerun this step
    """
    force = luigi.BoolParameter(default=False)
    output_file = "dashboard.html"
    if force:
        os.remove(output_file)

    def requires(self):
        return [SyncRepo()]

    def output(self):
        return luigi.LocalTarget(self.output_file)

    def run(self):
        update_cmd = """
            python dashboard.py update -o {} --datadir data
        """.format(
            self.output().path
        )
        subprocess.call(shlex.split(update_cmd))


class WebSitePull(luigi.Task):
    """
    git pull the website repo
    """
    def output(self):
        return MockTarget("git_pull", mirror_on_stderr=True)

    def run(self):
        os.chdir(WEB_DIR)
        subprocess.call(["git", "pull"])
        with self.output().open("w") as out:
            print("git pull", file=out)


class UpdateWebSite(luigi.Task):
    """
    copy the newly made dashboard.html to website repo

    :param force (bool): remove the dashboard html file from website repo for rerunning
    """
    force = luigi.BoolParameter(default=False)
    output_file = WEB_DIR + "/_includes/COVID.html"
    if force:
        os.remove(output_file)

    def requires(self):
        return [WebSitePull(), UpdateDashboard(force=self.force)]

    def output(self):
        return luigi.LocalTarget(self.output_file)

    def run(self):
        with self.output().open("w") as outfile:
            with UpdateDashboard().output().open("r") as infile:
                for line in infile:
                    print(line.strip().replace("<!DOCTYPE html>", ""), file=outfile)


class PushWebSite(luigi.Task):
    force = luigi.BoolParameter(default=False)

    def requires(self):
        return [UpdateWebSite(force=self.force)]

    def output(self):
        return MockTarget("git_push", mirror_on_stderr=True)

    def run(self):
        cmd = 'git commit -am "updated {}"'.format(TODAY)
        os.chdir(WEB_DIR)
        subprocess.call(shlex.split(cmd))
        subprocess.call(["git", "push"])
        with self.output().open("w") as out:
            print(cmd, file=out)


def date_range(date1, date2):
    """
    copy from https://www.w3resource.com/python-exercises/date-time-exercise/python-date-time-exercise-50.php

    :param date1 (datetime.date): first starting date of the range
    :param date2 (datetime.date): ending date of the range
    """
    for n in range(int((date2 - date1).days) + 1):
        yield date1 + timedelta(n)


if __name__ == "__main__":
    luigi.build(
        [PushWebSite(force=True)],
        local_scheduler=True,
        log_level="INFO",
        workers=4,
    )
