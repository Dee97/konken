import os
import requests
from linebot import LineBotApi
from linebot.models import (
    RichMenu, RichMenuSize
)

from django.conf import (
    settings
)

# line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)


def create_menu(menus, cramschool,img_type="png"):
    """
        Generates a rich menu based on the given template and image inside the rich_menu folder

        Args:
            menus(json): json template of the rich menu
            base_path(string): location of the image to be used in the rich menu
            img_type(string): default is "png"; image type of the image to be used in the rich menu

        Returns:
            result_ids(list of strings): ids of the rich menus that were generated 
    """
    line_bot_api = LineBotApi(cramschool.line_channel_access_token)
    result_ids = dict()
    for filename, template in menus.items():
        print("Processing", filename)
        try:
            rich_menu_to_create = RichMenu(
                size=RichMenuSize(width=template["size"]["width"], height=template["size"]["height"]),
                selected=template["selected"],
                name=template["name"],
                chat_bar_text=template["chatBarText"],
                areas=template["areas"]
            )

            menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
            print(template["name"], " -> ", menu_id)
            result_ids[template["name"]] = menu_id

            # upload image and use it for the rich menu
            # with open(os.path.join(base_path, f"{filename}.{img_type}"), 'rb') as img_file:
            #     line_bot_api.set_rich_menu_image(rich_menu_id=menu_id, content_type=f"image/{img_type}", content=img_file)

            with open(cramschool.rich_menu_img.path, 'rb') as img_file:
                line_bot_api.set_rich_menu_image(rich_menu_id=menu_id, content_type=f"image/{img_type}", content=img_file)

            print("===" * 20)
        except Exception as e:
            print(e)
            continue

        # set the default rich menu via post request
        url = f"https://api.line.me/v2/bot/user/all/richmenu/{menu_id}"
        # response = requests.post(url, headers={"Authorization": "Bearer " + settings.LINE_CHANNEL_ACCESS_TOKEN})
        response = requests.post(url, headers={"Authorization": "Bearer " + cramschool.line_channel_access_token})
        print(f"response code: {response.status_code}")

    print("results:", result_ids)
    return result_ids

