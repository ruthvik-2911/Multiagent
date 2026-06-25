from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

WATCH_FOLDER = "data"


class MyHandler(FileSystemEventHandler):

    def on_created(self, event):

        if not event.is_directory:

            print(f"\nNEW FILE DETECTED:")
            print(event.src_path)

    def on_modified(self, event):

        if not event.is_directory:

            print(f"\nFILE MODIFIED:")
            print(event.src_path)


event_handler = MyHandler()

observer = Observer()

observer.schedule(
    event_handler,
    WATCH_FOLDER,
    recursive=True
)

observer.start()

print("Watching folders...")

try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    observer.stop()

observer.join()
