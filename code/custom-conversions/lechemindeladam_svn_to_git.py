"""
The svn is too big to be automatically imported to git (and Github) because there are lots of large binary data components.
Needs a manual solution.

TODO use git lfs migrate later on the elements
TODO instead of svn export for every revision, checkout and then update to revision (reduced bandwith)
"""

import json
import sys
import psutil

from utils.utils import *


def remove_folders(base_folder, names):
    if isinstance(names, str):
        names = (names,)
    for name in names:
        folder = base_folder / name
        if folder.is_dir():
            shutil.rmtree(folder)


def remove_files(base_folder, names):
    if isinstance(names, str):
        names = (names,)
    for name in names:
        file = base_folder / name
        if os.path.isfile(file):
            os.remove(file)


def special_treatment(destination, revision):
    """

    """

    # copy content of trunk to base
    if 2270 <= revision <= 2420:
        source = destination / 'trunk'
        if source.is_dir():
            copy_tree(source, destination)
            shutil.rmtree(source)

    # copy all important files from Holyspirit/Holyspirit and delete it
    if 5 <= revision <= 330:
        source = destination / 'Holyspirit', 'Holyspirit'
        if source.is_dir():
            if revision >= 8:
                shutil.copytree(source / 'Data', destination / 'Data')
            files = [x for x in source.iterdir() if x.endswith('.txt')]
            for file in files:
                shutil.copy(source / file, destination)
            # remove it
            shutil.rmtree(destination / 'Holyspirit')

    # copy all important files from Holyspirit and delete it
    if 337 <= revision <= 2268:
        source = destination / 'Holyspirit'
        if source.is_dir():
            data = source / 'Data'
            if data.is_dir():
                # shutil.copytree(data, destination / 'Data')
                shutil.move(data, destination)
            target = destination / 'Meta'
            if not target.is_dir():
                target.mkdir()
            files = [x for x in source.iterdir() if x.endswith('.txt') or x.endswith('.conf') or x.endswith('.ini')]
            for file in files:
                shutil.move(source / file, target)
            # remove it
            shutil.rmtree(source)

    # copy data folder vom HolySpiritJE and delete it
    if 2012 <= revision <= 2269:
        source = destination / 'HolyspiritJE'
        if source.is_dir():
            data = source / 'Data'
            if data.is_dir():
                shutil.move(data, destination / 'DataJE')
            target = destination / 'MetaJE'
            if not target.is_dir():
                target.mkdir()
            files = [x for x in source.iterdir() if x.endswith('.txt') or x.endswith('.conf') or x.endswith('.ini')]
            for file in files:
                shutil.move(source / file, target)
            # remove it
            shutil.rmtree(source)

    # remove Holyspirit3 folder
    if 464 <= revision <= 2268:
        remove_folders(destination, 'Holyspirit3')

    # remove Holyspirit2 folder
    if 659 <= revision <= 2268:
        remove_folders(destination, 'Holyspirit2')

    # remove Launcher/release
    if 413 <= revision <= 2420:
        source = destination / 'Launcher'
        remove_folders(source, ('bin', 'debug', 'release', 'obj'))

    # delete all *.dll, *.exe in base folder
    if 3 <= revision <= 9:
        files = destination.iterdir()
        for file in files:
            if file.endswith('.exe') or file.endswith('.dll'):
                os.remove(destination / file)

    # delete "cross" folder
    if 42 <= revision <= 43:
        remove_folders(destination, 'Cross')

    # delete personal photos
    if 374 <= revision <= 2267:
        remove_folders(destination, 'Photos')
    if 2268 <= revision <= 2420:
        source = destination / 'Media'
        remove_folders(source, 'Photos')

    # move empire of steam out
    if 1173 <= revision <= 2420:
        folder = destination / 'EmpireOfSteam'
        if folder.is_dir():
            # move to empire path
            empire = empire_path / 'r{:04d}'.format(revision)
            shutil.move(folder, empire)

    # holy editor cleanup
    if 1078 <= revision <= 2420:
        source = destination / 'HolyEditor'
        remove_folders(source, ('bin', 'release', 'debug', 'obj'))
        remove_files(source, 'moc.exe')

    # source folder cleanup
    if 939 <= revision <= 2420:
        source = destination / 'Source'
        remove_folders(source, 'HS')
        remove_files(source, 'HS.zip')

    # sourceM folder cleanup
    if 2110 <= revision <= 2270:
        source = destination / 'SourceM'
        remove_folders(source, 'HS')

    # sourceNewApi cleanup
    if 2261 <= revision <= 2269:
        source = destination / 'SourceNewApi'
        remove_folders(source, 'HS')

    # Autres folder cleanup
    if 1272 <= revision <= 2267:
        source = destination / 'Autres'
        remove_folders(source, ('conf', 'db', 'hooks', 'locks'))
        remove_files(source, ('format', 'maj.php'))
    # Media/Other folder cleanup
    if 2268 <= revision <= 2420:
        source = destination / 'Media', 'Other'
        remove_files(source, ('format', 'maj.php'))

    # remove Holyspirit-Demo
    if 1668 <= revision <= 2268:
        remove_folders(destination, 'Holyspirit_Demo')

    # remove Debug.rar
    if 1950 <= revision <= 2420:
        remove_files(destination, 'Debug.rar')

    # remove 3dparty folder
    if 2273 <= revision <= 2420:
        remove_folders(destination, '3dparty')

    # branches cleanup
    if 2270 <= revision <= 2420:
        remove_folders(destination, 'branches')


def delete_global_excludes(folder):
    """

    """
    for dirpath, dirnames, filenames in os.walk(folder):
        rel_path = os.path.relpath(dirpath, folder)
        for file in filenames:
            if file in global_exclude:
                os.remove(dirpath / file)


def delete_empty_directories(folder):
    """

    """
    for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
        rel_path = os.path.relpath(dirpath, folder)
        if not filenames and not dirnames:
            os.removedirs(dirpath)


def list_large_unwanted_files(folder):
    """

    """
    output = []
    for dirpath, dirnames, filenames in os.walk(folder):
        rel_path = os.path.relpath(dirpath, folder)
        for file in filenames:
            file_path = dirpath / file
            already_listed = False
            for extension in unwanted_file_extensions:
                if file.endswith(extension):
                    output.append(rel_path / file + ' ' + str(os.path.getsize(file_path)))
                    already_listed = True
                    break
            if not already_listed and os.path.getsize(file_path) > large_file_limit:
                output.append(rel_path / file + ' ' + str(os.path.getsize(file_path)))
    return output


def checkout(revision_start, revision_end=None):
    """

    """
    if not revision_end:
        revision_end = revision_start

    assert revision_end >= revision_start

    for revision in range(revision_start, revision_end + 1):
        # check free disc space
        if psutil.disk_usage(svn_checkout_path).free < 3e10:  # 1e10 = 10 GiB
            print('not enough free disc space, will exit')
            sys.exit(-1)

        print('checking out revision {}'.format(revision))

        # create destination directory
        destination = svn_checkout_path / 'r{:04d}'.format(revision)
        if destination.exists():
            shutil.rmtree(destination)

        # checkout
        start_time = time.time()
        # sometimes checkout fails for reasons like "svn: E000024: Can't open file '/svn/p/lechemindeladam/code/db/revs/1865': Too many open files", we try again and again in these cases
        while True:
            try:
                subprocess_run(['svn', 'export', '-r{}'.format(revision), svn_url, destination])
                break
            except:
                print('problem with export, will try again')
                if destination.is_dir():
                    shutil.rmtree(destination)

        print('checkout took {:.1f}s'.format(time.time() - start_time))


def fix_revision(revision_start, revision_end=None):
    """

    """
    if not revision_end:
        revision_end = revision_start
    assert revision_end >= revision_start

    unwanted_files = {}
    sizes = {}

    for revision in range(revision_start, revision_end + 1):
        print('fixing revision {}'.format(revision))

        # destination directory
        destination = svn_checkout_path / 'r{:04d}'.format(revision)
        if not destination.exists():
            raise RuntimeError('cannot fix revision {}, directory does not exist'.format(revision))

        # special treatment
        special_treatment(destination, revision)

        # delete files from global exclude list
        delete_global_excludes(destination)

        # list unwanted files
        unwanted_files[revision] = list_large_unwanted_files(destination)

        # delete empty directories
        delete_empty_directories(destination)

        # size of resulting folder
        sizes[revision] = folder_size(destination)

    text = json.dumps(unwanted_files, indent=1)
    write_text(svn_checkout_path / 'unwanted_files.json'.format(revision), text)
    text = json.dumps(sizes, indent=1)
    write_text(svn_checkout_path / 'folder_sizes.json'.format(revision), text)


def initialize_git():
    """

    """
    # git init
    git_path.mkdir()
    os.chdir(git_path)
    subprocess_run(['git', 'init'])
    subprocess_run(['git', 'config', 'user.name', 'Trilarion'])
    subprocess_run(['git', 'config', 'user.email', 'Trilarion@users.noreply.gitlab.com'])


def combine_log_messages(msg):
    """

    """
    # throw out all empty ones
    msg = [x.strip() for x in msg if x]
    # combine again
    msg = "\r\n".join(msg)
    return msg


def read_logs():
    """
    Probably regular expressions would have worked too.
    """
    # read log
    print('read all log messages')
    os.chdir(svn_checkout_path)
    start_time = time.time()
    log = subprocess_run(['svn', 'log', svn_url], display=False)
    print('read log took {:.1f}s'.format(time.time() - start_time))
    # process log
    log = log.split('\r\n------------------------------------------------------------------------\r\n')
    # not the last one
    log = log[:-2]
    print('{} log entries'.format(len(log)))

    # process log entries
    log = [x.split('\r\n') for x in log]

    # the first one still contains an additional "---" elements
    log[0] = log[0][1:]

    # split the first line
    info = [x[0].split('|') for x in log]

    # get the revision
    revision = [int(x[0][1:]) for x in info]

    author = [x[1].strip() for x in info]
    unique_authors = list(set(author))
    unique_authors.sort()

    date = [x[2].strip() for x in info]
    msg = [combine_log_messages(x[2:]) for x in log]
    logs = list(zip(revision, author, date, msg))
    logs.sort(key=lambda x: x[0])
    return logs, unique_authors


def gitify(revision_start, revision_end):
    """

    """
    assert revision_end >= revision_start

    for revision in range(revision_start, revision_end + 1):
        print('adding revision {} to git'.format(revision))

        # svn folder
        svn_folder = svn_checkout_path / 'r{:04d}'.format(revision)
        if not svn_folder.exists():
            raise RuntimeError('cannot add revision {}, directory does not exist'.format(revision))

        # clear git path
        print('git clear path')
        while True:
            try:
                git_clear_path(git_path)
                break
            except PermissionError as e:
                print(e)
                # wait a bit
                time.sleep(1)

        # copy source files to git path
        print('copy to git')
        copy_tree(svn_folder, git_path)

        os.chdir(git_path)

        # update the git index (add unstaged, remove deleted, ...)
        print('git add')
        subprocess_run(['git', 'add', '--all'])

        # check if there is something to commit
        status = subprocess_run(['git', 'status', '--porcelain'])
        if not status:
            print(' nothing to commit for revision {}, will skip'.format(revision))
            continue

        # perform the commit
        print('git commit')
        log = logs[revision]  # revision, author, date, message
        message = log[3] + '\r\nsvn-revision: {}'.format(revision)
        print('  message "{}"'.format(message))
        author = authors[log[1]]
        author = '{} <{}>'.format(*author)
        cmd = ['git', 'commit', '--allow-empty-message', '--message={}'.format(message), '--author={}'.format(author),
               '--date={}'.format(log[2])]
        print('  cmd: {}'.format(' '.join(cmd)))
        subprocess_run(cmd)


if __name__ == "__main__":

    global_exclude = ['Thumbs.db']
    unwanted_file_extensions = ['.exe', '.dll']
    large_file_limit = 1e6  # in bytes

    # base path is the directory containing this file
    base_path = pathlib.Path(__file__) / 'conversion'
    print('base path={}'.format(base_path))

    # derived paths
    svn_checkout_path = base_path / 'svn'
    if not svn_checkout_path.exists():
        svn_checkout_path.mkdir()
    empire_path = base_path / 'empire'  # empire of steam side project
    if not empire_path.exists():
        empire_path.mkdir()
    git_path = base_path / 'lechemindeladam'
    if not git_path.exists():
        initialize_git()

    # svn url
    svn_url = "https://svn.code.sf.net/p/lechemindeladam/code/"

    # read logs
    # logs, authors = read_logs()
    # text = json.dumps(logs, indent=1)
    # write_text(base_path / 'logs.json', text)
    # text = json.dumps(authors, indent=1)
    # write_text(base_path / 'authors.json', text)
    text = read_text(base_path / 'logs.json')
    logs = json.loads(text)
    logs = {x[0]: x for x in logs}  # dictionary
    text = read_text(base_path / 'authors.json')
    authors = json.loads(text)  # should be a dictionary: svn-author: [git-author, git-email]

    # the steps
    # checkout(1, 50)
    # fix_revision(1, 50)
    # gitify(4, 50)

    # checkout(51, 100)
    # checkout(101, 200)

    # fix_revision(51, 200)

    # gitify(51, 200)

    # checkout(201, 400)
    # fix_revision(201, 400)
    # gitify(201, 400)

    # checkout(401, 800)
    # fix_revision(401, 800)
    # gitify(401, 800)

    # checkout(801, 1200)
    # fix_revision(801, 1200)
    # gitify(801, 1200)

    # checkout(1201, 1470)
    # fix_revision(1201, 1470)
    # gitify(1201, 1470)

    # checkout(1471, 1700)
    # fix_revision(1471, 1700)
    # gitify(1471, 1700)

    # checkout(1701, 1900)
    # fix_revision(1701, 1900)
    # gitify(1701, 1900)

    # checkout(1901, 2140)
    # fix_revision(1901, 2140)
    # gitify(1901, 2140)

    # checkout(2141, 2388)
    # fix_revision(2141, 2388)
    # gitify(2141, 2388)

    # checkout(2389, 2420)
    # fix_revision(2389, 2420)
    # gitify(2389, 2420)

    # run the following commands in the git bash
    # git config credential.useHttpPath true
    # git lfs install
    # git lfs migrate import --include-ref=master --include="Zombie_paysan.rs.hs,Witch_monster.rs.hs,WanderingStones.rs.hs,TwoWeapons.rs.hs,TwoHands.rs.hs,TwoHand.rs.hs,Reaper.rs.hs,Peasant_crossbow.rs.hs,Peasant_club.rs.hs,OneHand.rs.hs,Offspring_champion.rs.hs,Mimic.rs.hs,LordSkeleton.rs.hs,Goule.rs.hs,ErrantRoche.rs.hs,DemonicPriest0.rs.hs,DemonicPriest.rs.hs,Brute.rs.hs,20575__dobroide__20060706.night.forest02.wav,31464__offtheline__Morning_Sounds.wav,47989__Luftrum__forestsurroundings.wav,ambiance.wav,Catacombs0.wav,Pluie.wav,Taverne fusion.png,Abbey.ogg,AgrarianLands0.ogg,AgrarianLands1.ogg,Boss0.ogg,Catacombs0.ogg,Catacombs1.ogg,DarkForest.ogg,Forest_ambient0.ogg,Johannes.ogg,OWC.ogg"

    # then add remote and push (done)
