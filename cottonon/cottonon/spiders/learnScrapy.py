import scrapy
import logging
from bs4 import BeautifulSoup
from math import ceil

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


class CottononSpider(scrapy.Spider):
    name = "cottonon"
    allowed_domains = ["cottonon.com/"]
    start_urls = [
        "https://cottonon.com/AU/"
    ]

    def parse(self, response, get_menu_items=False, x=False):
        # print("aaaaa")
        if not x:
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

                    print("ASDASDFDFDSFDSS", len(categories_of_products))
                    # categories_of_products is a set of links like:
                    # https://cottonon.com/AU/women/womens-activewear/
                    # https://cottonon.com/AU/women/womens-activewear/womens-gym-tops/
                    # https://cottonon.com/AU/women/womens-activewear/womens-gym-bottoms/
                    # https://cottonon.com/AU/women/womens-activewear/womens-gym-crop-tops-bras/
                    # https://cottonon.com/AU/women/womens-activewear/womens-gym-active-fleece/
                    # https://cottonon.com/AU/women/womens-activewear/womens-running-jackets-vests/
                    for link_to_category in categories_of_products[1:]:  # TODO: 0:4 is just for dev. 0: for finished product
                        print("LINK:", link_to_category)
                        yield scrapy.Request(link_to_category, callback=self.start_parsing_category, dont_filter=True,
                                             meta={"link_to_category": link_to_category})
                        exit()

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
        total_entries_in_category = response.xpath().extract(path_to_total_entries)[0].strip("\n").split(" ")[0]
        print("T:", total_entries_in_category)
        pages = ceil(total_entries_in_category / 48)
        # assemble list of links for spider to visit
        base_url_for_category = response.meta["link_to_category"]
        links_to_pages_in_this_category = []
        for page_number in range(1, pages + 1):
            paginated_links = base_url_for_category + "?start=" + page_number * 48 + "&sz=48"
            links_to_pages_in_this_category.append(paginated_links)

        # ### Handle the first page in the category, which we are already on.
        # "product_divs"
        tile_path = "//div[@class='product-tile']"
        # gets between 1 and 48 SelectorLists, depending on how many products are on the page.
        product_tiles_from_the_page = response.xpath(tile_path)
        # FIXME: this naming seems wrong. it's feeding pages into the for loop, so its name should be "pages" ... and yet i was expecting tiles?
        all_products_from_category = []
        for page in product_tiles_from_the_page[0:1]:  # TODO: remove 0:3 when done developing. its just there to make things run faster
            new_products = self.convert_product_tiles_from_this_page_to_items(page)  # FIXME: this is currently printing an item that contains the name of every product on the page.
            all_products_from_category.append(new_products)

        # ### send Scrapy to handle the rest of the pages in the category, sans the first page, which is done
        # TODO: must get Scrapy to send the products from that page back to this function...
        for remaining_link in links_to_pages_in_this_category[1:]:
            yield scrapy.Request(remaining_link, self.parse_products_on_this_page, dont_filter=True,
                                 meta={"past_first_page": True})

        return all_products_from_category

    def convert_product_tiles_from_this_page_to_items(self, product_tiles_from_the_page):
        """takes a Selector containing a product and converts it into an Item"""
        product_tile_path = "//div[@class='product-tile']"
        product_name_path = "//div[@class='product-name']/a[@class='name-link']/text()"
        product_price_path = "//div[@class='product-pricing ']/span[@class='product-sales-price']/text()"
        product_colors_path = "//div[@class='product-colors']/div[@class='product-colours-available']/span/text()"

        # 1 to 48 SelectorLists and Selectors returned
        selector_list_of_products = product_tiles_from_the_page.xpath("//li[@class='grid-tile columns']")
        # print("HEORISFSIFDNSFODNSFODSFLDSNFDSFDSFDSFDSFS", len(selector_list_of_products), type(selector_list_of_products), type(selector_list_of_products[0]))

        products_from_page = []
        for product in selector_list_of_products:  # fixme; remove 0:5 after dev
            # FIXME: current problem is, it seems I misunderstand something, as the selector_list_of_products var
            # ... that i expect to contain a list of products from a single page...
            # ... unleashes a list like 40 entries, only 3 of which are unique; the rest are copies. why? idgi
            # print(type(product))
            name = product.xpath(product_tile_path + product_name_path).extract()
            price = product.xpath(product_tile_path + product_price_path).extract()
            colors = product.xpath(product_tile_path + product_colors_path).extract()
            for n, p, c in zip(name, price, colors):
                products_from_page.append(Product(name=n, price=p, colors=c))

        return products_from_page
