import re

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from adumbra.config import CONFIG
from adumbra.database import ImageModel
from adumbra.webserver.util.thumbnails import generate_thumbnail


class ImageFolderHandler(FileSystemEventHandler):

    PREFIX = "[File Watcher]"

    def __init__(self, pattern=None):
        self.pattern = pattern or ImageModel.PATTERN

    def on_any_event(self, event):

        path = event.dest_path if event.event_type == "moved" else event.src_path

        if event.is_directory:
            # Listen to directory events as some file systems don't generate
            # per-file `deleted` events when moving/deleting directories
            if event.event_type == "deleted":
                self._log(f"Deleting images from adumbra.database {path}")
                ImageModel.objects(path=re.compile("^" + re.escape(path))).delete()
            return

        if (
            # check if its a hidden file
            bool(re.search(r"\/\..*?\/", path))
            or not path.lower().endswith(self.pattern)
        ):
            return

        self._log(f"File {path} for {event.event_type}")

        image = ImageModel.objects(path=event.src_path).first()

        if image is None and event.event_type != "deleted":
            self._log(f"Adding new file to database: {path}")
            image = ImageModel.create_from_path(path).save()
            generate_thumbnail(image)

        elif event.event_type == "moved":
            self._log(f"Moving image from {event.src_path} to {path}")
            image.update(path=path)
            generate_thumbnail(image)

        elif event.event_type == "deleted":
            self._log(f"Deleting image from adumbra.database {path}")
            ImageModel.objects(path=path).delete()

    def _log(self, message):
        print(f"{self.PREFIX} {message}", flush=True)


def run_watcher():
    observer = Observer()
    observer.schedule(ImageFolderHandler(), CONFIG.dataset_directory, recursive=True)
    observer.start()
