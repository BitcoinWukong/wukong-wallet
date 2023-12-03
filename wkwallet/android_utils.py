from typing import List

from kivy import platform
from kivy.logger import Logger

if platform == "android":
    from android import activity  # type: ignore
    from jnius import autoclass, cast

    Activity = autoclass("android.app.Activity")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    currentActivity = cast("android.app.Activity", PythonActivity.mActivity)


ACTION_SAVE_FILE = 1
ACTION_READ_FILE = 2


def android_save_string_to_file(file_name, content_str):
    if platform != "android":
        return

    def on_activity_save(request_code, result_code, intent):
        activity.unbind(on_activity_result=on_activity_save)
        if request_code != ACTION_SAVE_FILE:
            Logger.info(
                "on_activity_save: ignoring activity result that was not ACTION_SAVE_FILE"
            )
            return

        if result_code == Activity.RESULT_CANCELED:
            return
        if result_code != Activity.RESULT_OK:
            Logger.error('Unknown result_code "{}"'.format(result_code))
            raise NotImplementedError('Unknown result_code "{}"'.format(result_code))

        selectedUri = intent.getData()
        Logger.info(f"Saving to file: {selectedUri.toString()}")
        _android_do_saving(selectedUri, content_str)

    intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("text/plain")
    intent.putExtra(Intent.EXTRA_TITLE, file_name)
    activity.bind(on_activity_result=on_activity_save)
    currentActivity.startActivityForResult(intent, ACTION_SAVE_FILE)


def _android_do_saving(uri, content_str):
    FileOutputStream = autoclass("java.io.FileOutputStream")

    bytedata = bytes(content_str, "utf-8")

    try:
        # For writing, it is important to get ParcelFileDescriptor from ContentResolver ...
        pfd = currentActivity.getContentResolver().openFileDescriptor(uri, "w")

        # ... because from ParcelFileDescriptor you need to use getFileDescriptor() function,
        # which will allow us to create a FileOutputStream (and not a regular OutputStream), ...
        fos = FileOutputStream(pfd.getFileDescriptor())

        # ... because FileOutputStream can access the OutputStream channel,
        fos_ch = fos.getChannel()

        # ... so that after writing data to a file ...
        fos.write(bytedata)

        # ... this channel was able to cut off extra bytes if the number of newly written bytes was less than in the file being rewritten.
        fos_ch.truncate(len(bytedata))

        fos.close()

        print("Saving bytedata succeeded.")
    except:
        print("Saving bytedata failed.")


def android_open_file(callback):
    if platform != "android":
        return

    def on_activity_read(request_code, result_code, intent):
        activity.unbind(on_activity_result=on_activity_read)
        if request_code != ACTION_READ_FILE:
            Logger.warning(
                "on_activity_read: ignoring activity result that was not ACTION_READ_FILE"
            )
            return

        if result_code == Activity.RESULT_CANCELED:
            return
        if result_code != Activity.RESULT_OK:
            Logger.error('Unknown result_code "{}"'.format(result_code))
            raise NotImplementedError('Unknown result_code "{}"'.format(result_code))

        selectedUri = intent.getData()
        Logger.info(f"Reading from file: {selectedUri.toString()}")
        callback(_android_do_reading(selectedUri))

    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("*/*")
    activity.bind(on_activity_result=on_activity_read)
    currentActivity.startActivityForResult(intent, ACTION_READ_FILE)


def _android_do_reading(uri) -> List[str]:
    result = []

    FileInputStream = autoclass("java.io.FileInputStream")
    InputStreamReader = autoclass("java.io.InputStreamReader")
    BufferedReader = autoclass("java.io.BufferedReader")

    try:
        # For writing, it is important to get ParcelFileDescriptor from ContentResolver ...
        pfd = currentActivity.getContentResolver().openFileDescriptor(uri, "r")

        # ... because from ParcelFileDescriptor you need to use getFileDescriptor() function,
        # which will allow us to create a FileOutputStream (and not a regular OutputStream), ...
        fstream = FileInputStream(pfd.getFileDescriptor())

        br = BufferedReader(InputStreamReader(fstream))
        l = br.readLine()
        while l:
            Logger.debug(l)
            result.append(l)
            l = br.readLine()
        fstream.close()

        print("Read data succeeded.")
    except:
        print("Read data failed.")
    return result
