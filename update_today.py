import os
from datetime import date, timedelta
import subprocess
import shlex
import logging
from pathlib import Path
from git import Repo

import luigi
from luigi.mock import MockTarget

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s || %(levelname)s  || %(name)s || %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Update")

FILE = Path(__file__).absolute()
WORKING_DIR = os.path.dirname(FILE)
WEB_DIR = WORKING_DIR.parent / "wckdouglas.github.io"
FIRST_DAY = date(2020, 4, 12)
TODAY = date.today()


class GetData(luigi.Task):
    """
    For a given date (e.g. "2021-05-01"), retrieve data and save it to data/
    """

    day = luigi.Parameter()

    def rquires(self):
        return [CovidPull()]

    def output(self):
        return luigi.LocalTarget(WORKING_DIR / "data/{}.tsv".format(self.day))

    def run(self):  # work if SGE
        cmd = "python dashboard.py get --date {}".format(self.day)
        logger.debug("Getting {}".format(self.output().path))
        with self.output().open("w") as out:
            subprocess.run(shlex.split(cmd), stdout=out)


class CovidPull(luigi.Task):
    """
    git pull the covid data repo
    """
    def output(self):
        return MockTarget("git_pull_covid", mirror_on_stderr=True)

    def run(self):
        git_sync(WORKING_DIR, action="pull")

        with self.output().open("w") as out:
            print('git pulled covid', file=out)


class SyncRepo(luigi.Task):
    """
    2. git add the newly added file in data/
    3. git push
    """

    def output(self):
        return MockTarget("git_dashboard", mirror_on_stderr=True)

    def requires(self):
        return [GetData(day=str(day)) for day in date_range(FIRST_DAY, TODAY)]

    def run(self):
        with Repo(WORKING_DIR) as repo:
            index = repo.index
            for task in self.requires():
                if os.stat(task.output().path).st_size > 0:
                    index.add(task.output().path)
                    logger.info("Added {}".format(task.output().path))
            index.commit('Added %s' %task.output().path)
        git_sync(WORKING_DIR, action="push")

        with self.output().open("w") as out:
            print("git_push", file=out)


class UpdateDashboard(luigi.Task):
    """
    refresh the dash board

    :param force (bool): remove the existing dashboard.html and rerun this step
    """

    force = luigi.BoolParameter(default=False)
    output_file = "dashboard.html"
    if force and os.path.isfile(output_file):
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
        return MockTarget("git_pull_website", mirror_on_stderr=True)

    def run(self):
        git_sync(WEB_DIR, action="pull")

        with self.output().open("w") as out:
            print("git pull website", file=out)


class UpdateWebSite(luigi.Task):
    """
    copy the newly made dashboard.html to website repo

    :param force (bool): remove the dashboard html file from website repo for rerunning
    """

    force = luigi.BoolParameter(default=False)
    output_file = WEB_DIR  / "_includes/COVID.html"
    if force and os.path.isfile(output_file):
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
        os.chdir(WEB_DIR)
        with Repo(WEB_DIR) as web_repo:
            web_repo.index.commit("Updated {}".format(TODAY))
        git_sync(WEB_DIR, action="push")
        with self.output().open("w") as out:
            print("pushed website", file=out)


def date_range(date1, date2):
    """
    copy from https://www.w3resource.com/python-exercises/date-time-exercise/python-date-time-exercise-50.php

    :param date1 (datetime.date): first starting date of the range
    :param date2 (datetime.date): ending date of the range
    """
    for n in range(int((date2 - date1).days) + 1):
        yield date1 + timedelta(n)


def git_sync(dir: str, action: str = "pull"):
    """
    do a git pull in the give directory

    :param dir (str): a git directory
    :param action (str): {'pull','push'}
    """

    assert action in {"pull", "push"}
    with Repo(dir) as repo:
        for remote in repo.remotes:
            if remote.name == "origin":
                if action == "pull":
                    remote.pull()
                else:
                    remote.push()
                logger.info("git {} {}".format(action, dir))


if __name__ == "__main__":

    luigi.build(
        [PushWebSite(force=True)],
        local_scheduler=False,
        log_level="INFO",
        workers=4,
        detailed_summary=True,
        scheduler_port=2020,
    )
