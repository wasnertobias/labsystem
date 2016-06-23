import re
import os
import io
import shutil

from git import Repo, cmd

from app import app

shaRegex = re.compile('[a-f0-9]{40}')


def read(course, branch, path):
    if shaRegex.match(branch) is not None:
        repo = Repo(os.path.join(app.config['COURSES_DIR'], course, 'master'))
        blob = repo.commit(branch).tree[path]
        return io.BytesIO(blob.data_stream.read())
    else:
        return io.open(os.path.join(app.config['COURSES_DIR'], course, branch, path), 'rb')


class GitStorageError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def write(course, branch, path):
    if shaRegex.match(branch):
        raise GitStorageError('Can only write to checked out branches')

    return io.open(os.path.join(app.config['COURSES_DIR'], course, branch, path), 'w')


def delete(course, branch, path):
    if shaRegex.match(branch):
        raise GitStorageError('Can only delete from checked out branches')

    os.remove(os.path.join(app.config['COURSES_DIR'], course, branch, path))


def rename(course, branch, path, newpath):
    if shaRegex.match(branch):
        raise GitStorageError('Can only rename files in checked out branches')

    os.rename(os.path.join(app.config['COURSES_DIR'], course, branch, path), os.path.join(app.config['COURSES_DIR'], course, branch, newpath))


def deleteDirectory(course, branch, path):
    if shaRegex.match(branch):
        raise GitStorageError('Can only delete from checked out branches')

    shutil.rmtree(os.path.join(app.config['COURSES_DIR'], course, branch, path))


def createDirectory(course, branch, path):
    if shaRegex.match(branch):
        raise GitStorageError('Can only delete from checked out branches')

    os.makedirs(os.path.join(app.config['COURSES_DIR'], course, branch, path))


def createBranch(course, source, to):
    repo = Repo(os.path.join(app.config['COURSES_DIR'], course, 'master'))
    repo.create_head(to, source)

    repo.git.worktree('add', os.path.abspath(os.path.join(app.config['COURSES_DIR'], course, to)), to)


def mergeBranches(course, branch, source):
    if shaRegex.match(source):
        raise GitStorageError('Can only merge branches')

    git = cmd.Git(os.path.join(app.config['COURSES_DIR'], course, branch))

    git.merge(source)


def deleteBranch(course, branch):
    repo = Repo(os.path.join(app.config['COURSES_DIR'], course, 'master'))
    repo.delete_head(branch)
    shutil.rmtree(os.path.join(app.config['COURSES_DIR'], course, branch))


def listCheckedOutBranches(course):
    return os.listdir(os.path.join(app.config['COURSES_DIR'], course))


def listAvailableBranches(course):
    repo = Repo(os.path.join(app.config['COURSES_DIR'], course, 'master'))
    return map(lambda x: str(x), repo.heads)


def createCourse(course):
    os.makedirs(os.path.join(app.config['COURSES_DIR'], course))
    repo = Repo.init(os.path.join(app.config['COURSES_DIR'], course, 'master'))
    os.makedirs(os.path.join(app.config['COURSES_DIR'], course, 'master', 'content'))
    os.makedirs(os.path.join(app.config['COURSES_DIR'], course, 'master', 'secret'))

    stream = io.open(os.path.join(app.config['COURSES_DIR'], course, 'master', 'course.meta'), 'w+')
    stream.write("type: Course\nchildren: []\nshowOnlyHeaders: true")
    stream.close()

    repo.git.add('course.meta')
    repo.git.commit('-m', 'Initial commit')


def deleteCourse(course):
    shutil.rmtree(os.path.join(app.config['COURSES_DIR'], course))


def renameCourse(course, newcourse):
    os.rename(os.path.join(app.config['COURSES_DIR'], course), os.path.join(app.config['COURSES_DIR'], newcourse))


def listCourses():
    return os.listdir(app.config['COURSES_DIR'])


def getHistory(course, branch, paths, offset, limit):
    repo = Repo(os.path.join(app.config['COURSES_DIR'], course, 'master'))
    return repo.iter_commits(branch, paths, max_count=limit, skip=offset)


def isRepoDirty(course, branch):
    if shaRegex.match(branch):
        return False

    git = cmd.Git(os.path.join(app.config['COURSES_DIR'], course, branch))

    return len(git.diff()) > 0


def commit(course, branch, message, user):
    if shaRegex.match(branch):
        raise GitStorageError('Can only commit on branches')

    git = cmd.Git(os.path.join(app.config['COURSES_DIR'], course, branch))

    git.add('.')
    git.commit('-m', message, "--author", user.name + '<' + user.email + '>')
