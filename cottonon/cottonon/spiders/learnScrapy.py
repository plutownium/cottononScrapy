import scrapy
import logging
from bs4 import BeautifulSoup
from math import ceil
import requests
import json

logging.getLogger('scrapy').propagate = False

# The script should:
# 1) Get all product metadata
# 2) Get all product images
# 3) Be readable
#
# Extra credit: Provide an argument to get the menu items (hard).

class Product(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    colors = scrapy.Field()
    img_links = scrapy.Field()
    ratings = scrapy.Field()


class CottononSpider(scrapy.Spider):
    name = "cottonon"
    allowed_domains = ["cottonon.com/"]
    start_urls = [
        "https://cottonon.com/AU/"
    ]

    def parse(self, response, get_menu_items=False):
        # print("aaaaa")

        menu_items_to_print = []
        for menu_item in response.css('.menu-item'):
            menu_item_to_filter = menu_item.get()
            # print("bbbbbbbbbbbbbbb")
            if "Women|" in menu_item_to_filter:
                # print("\n-------\n-------")
                categories_of_products = menu_item.css('a::attr(href)').getall()

                if get_menu_items:  # flag
                    for title in menu_item.css('a::attr(data-gtag)').getall():
                        menu_items_to_print.append(title)

                # print("ASDASDFDFDSFDSS", len(categories_of_products))
                # categories_of_products is a set of links like:
                # https://cottonon.com/AU/women/womens-activewear/
                # https://cottonon.com/AU/women/womens-activewear/womens-gym-tops/
                # https://cottonon.com/AU/women/womens-activewear/womens-gym-bottoms/
                # https://cottonon.com/AU/women/womens-activewear/womens-gym-crop-tops-bras/
                # https://cottonon.com/AU/women/womens-activewear/womens-gym-active-fleece/
                # https://cottonon.com/AU/women/womens-activewear/womens-running-jackets-vests/
                for link_to_category in categories_of_products[1:]:  # TODO: 0:4 is just for dev. 0: for finished product
                    # print("LINK:", link_to_category)
                    category = str(link_to_category)[29:]
                    yield scrapy.Request(link_to_category, callback=self.start_parsing_category, dont_filter=True,
                                         meta={"link_to_category": link_to_category, "category_name": category})
                    # exit()

        # output file of menu items
        with open("menu_items.txt", "w") as f:
            for entry in menu_items_to_print:
                f.write(entry)
                f.write("\n")

    def start_parsing_category(self, response):
        """ Used when the spider lands on the page of a product category.
        """
        # ### First thing to do is to get the # of pages in the category.
        # Note: suppose a category has 189 entries. There are 48 entries per page.
        # 189 / 48 = 3.93. There are 4 pages. Therefore, deploy a ceil() function.
        #
        path_to_total_entries = "//span[@class='paging-information-items']/text()"
        total_entries_in_category = response.xpath(path_to_total_entries).extract()[0].strip("\n").split(" ")[0]
        # print("T:", total_entries_in_category)
        pages = ceil(int(total_entries_in_category) / 48)
        # assemble list of links for spider to visit
        base_url_for_category = response.meta["link_to_category"]
        links_to_pages_in_this_category = []
        for page_number in range(1, pages + 1):
            start_value = page_number * 48
            paginated_links = base_url_for_category + "?start=" + str(start_value) + "&sz=48"
            links_to_pages_in_this_category.append(paginated_links)

        # ### Handle the first page in the category, which we are already on.
        # "product_divs"
        tile_path = "//div[@class='product-tile']"
        # gets between 1 and 48 SelectorLists, depending on how many products are on the page.
        product_tiles_from_the_page = response.xpath(tile_path)
        # FIXME: this naming seems wrong. it's feeding pages into the for loop, so its name should be "pages" ... and yet i was expecting tiles?
        for page in product_tiles_from_the_page[0:1]:  # TODO: remove 0:3 when done developing. its just there to make things run faster
            self.convert_product_tiles_from_this_page_to_items(page, product_category=response.meta["category_name"])
            # FIXME: this is currently printing an item that contains the name of every product on the page.

        # ### send Scrapy to handle the rest of the pages in the category, sans the first page, which is done
        page_num = 2
        for remaining_link in links_to_pages_in_this_category[1:]:
            # print(remaining_link)
            yield scrapy.Request(remaining_link, self.parse_further_pages, dont_filter=True,
                                 meta={"page_number": page_num})
            page_num = page_num + 1

        return None

    def convert_product_tiles_from_this_page_to_items(self, product_tiles_from_the_page, product_category, page_num=None):
        """takes a Selector containing a product and converts it into an Item"""
        product_tile_path = "//div[@class='product-tile']"
        product_name_path = "//div[@class='product-name']/a[@class='name-link']/text()"
        product_price_path = "//div[@class='product-pricing ']/span[@class='product-sales-price']/text()"
        product_colors_path = "//div[@class='product-colors']/div[@class='product-colours-available']/span/text()"
        product_link_path = "//div[@class='product-name']/a[@class='name-link']/@href"

        # 1 to 48 SelectorLists and Selectors returned
        selector_list_of_products = product_tiles_from_the_page.xpath("//li[@class='grid-tile columns']")
        # print("HEORISFSIFDNSFODNSFODSFLDSNFDSFDSFDSFDSFS", len(selector_list_of_products), type(selector_list_of_products), type(selector_list_of_products[0]))

        current_page = "first"
        if page_num:
            current_page = page_num

        products_from_page = []
        for product in selector_list_of_products:  # fixme; remove 0:5 after dev
            # FIXME: current problem is, it seems I misunderstand something, as the selector_list_of_products var
            # ... that i expect to contain a list of products from a single page...
            # ... unleashes a list like 40 entries, only 3 of which are unique; the rest are copies. why? idgi
            # print(type(product))
            name = product.xpath(product_tile_path + product_name_path).extract()
            price = product.xpath(product_tile_path + product_price_path).extract()
            colors = product.xpath(product_tile_path + product_colors_path).extract()
            individual_page_links = product.xpath(product_tile_path + product_link_path).extract()

            for n, p, c, link in zip(name, price, colors, individual_page_links):
                self.retrieve_ratings_and_images_from_product_page_and_write_file(link, n, p, c,
                                                                                  product_category,
                                                                                  current_page)
                # products_from_page.append(Product(name=n, price=p, colors=c, img_links=imgs, ratings=ratings))

        # TODO: have this func end by creating a .csv with products from this page
        # TODO: get product_category from parse and pass it on thru the functions
        # filename = product_category + "_-_" + "first_page" + ".csv"
        # if page_num:
        #     filename = product_category + "_-_" + str(page_num) + ".csv"
        # with open(filename, "w") as f:
        #     for product in products_from_page:
        #         csv_line = product.name + "," + product.price + "," + product.colors + "," + json.dumps(product.ratings) + "," + product.images
        #         f.write(csv_line)

        # i.e. product_category_-_product_page.csv
        return None

    def retrieve_ratings_and_images_from_product_page_and_write_file(self, link_to_page, name, price, colors, category, page_num):
        page = requests.get(link_to_page)
        soup = BeautifulSoup(page.text, "html.parser")

        product_image_tags = soup.find_all("img", {"class": "primary-image"})

        srcs = []
        for img in product_image_tags:
            srcs.append(img["src"])

        ratings_divs = soup.find_all("div", {"class": "bv-inline-histogram-ratings-score"})
        ratings = []
        stars = 5
        for div in ratings_divs:
            rating = {stars: div.find("span").get_text()}
            ratings.append(rating)
            stars = stars - 1

        filename = category.replace('/', "") + "_" +  page_num +  "_" + name.replace('\n', "") + ".csv"
        with open(filename, "w") as f:
            csv_line = name.replace("\n", "") + "," + price + "," + "".join(json.dumps(colors)) + "," + "".join(json.dumps(ratings)) + "," + ",".join(srcs)
            f.write(csv_line)
        return None

    def parse_further_pages(self, response):
        """
            Handles pages 2 and onward. Turns them into .csv files.
        :param response: This is the text of the page.
        :return: Nothing.
        """
        # print("Page num: ", response.meta["page_number"])
        page_num = response.meta["page_number"]
        tile_path = "//div[@class='product-tile']"
        # gets between 1 and 48 SelectorLists, depending on how many products are on the page.
        product_tiles_from_the_page = response.xpath(tile_path)  # fixme: again the strange "get page when expecting tiles"
        for page in product_tiles_from_the_page:
            self.convert_product_tiles_from_this_page_to_items(page,
                                                               product_category=response.meta["category_name"],
                                                               page_num=page_num)

        return None


