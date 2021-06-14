# (c) @AbirHasan2005

import shutil


async def delete_all(root: str):
    """
    Delete a Folder.

    :param root: Pass Folder Path as String.
    """

    try:
        shutil.rmtree(root)
    except Exception as e:
        print(e)
