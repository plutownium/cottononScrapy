import scrapy
import logging
from bs4 import BeautifulSoup

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
                        yield scrapy.Request(link_to_category, callback=self.start_parsing_category, dont_filter=True)
                        exit()

            # output file of menu items
            with open("menu_items.txt", "w") as f:
                for entry in menu_items_to_print:
                    f.write(entry)
                    f.write("\n")

    def start_parsing_category(self, response):
        """This method handles parsing at the level of product categories.
            So when the code gets here, the code is extracting the list of products displayed on the first page
            of the category.
        """
        # product_divs is
        tile_path = "//div[@class='product-tile']"
        # gets between 1 and 48 SelectorLists, depending on how many products are on the page.
        product_tiles_from_the_page = response.xpath(tile_path)

        # print("63: {}, {}".format(len(product_tiles_from_the_page), type(product_tiles_from_the_page)))
        for page in product_tiles_from_the_page[0:1]:  # TODO: remove 0:3 when done developing. its just there to make things run faster
            new_products = self.convert_product_tiles_from_this_page_to_items(page)  # FIXME: this is currently printing an item that contains the name of every product on the page.
        yield None

    def convert_product_tiles_from_this_page_to_items(self, product_tiles_from_the_page):
        """takes a Selector containing a product and converts it into an Item"""
        product_tile_path = "//div[@class='product-tile']"
        product_name_path = "//div[@class='product-name']/a[@class='name-link']/text()"
        product_price_path = "//div[@class='product-pricing']/span[@class='product-sales-price']/text()"
        product_colors_path = "//div[@class='product-colors']/span[@class='product-sales-price']/text()"

        # 1 to 48 SelectorLists and Selectors returned
        selector_list_of_products = product_tiles_from_the_page.xpath("//li[@class='grid-tile columns']")
        print("HEORISFSIFDNSFODNSFODSFLDSNFDSFDSFDSFDSFS", len(selector_list_of_products), type(selector_list_of_products), type(selector_list_of_products[0]))
        for product in selector_list_of_products[0:3]:  # fixme; remove 0:5 after dev
            # FIXME: current problem is, it seems I misunderstand something, as the selector_list_of_products var
            # ... that i expect to contain a list of products from a single page...
            # ... unleashes a list like 40 entries, only 3 of which are unique; the rest are copies. why? idgi
            print(type(product))
            name = product.xpath(product_tile_path + product_name_path).extract()
            price = product.xpath(product_tile_path + product_price_path).extract()
            colors = product.xpath(product_tile_path + product_colors_path).extract()
            print(len(name), name,price,colors)
            # soup = BeautifulSoup(product, "html.parser")
            # parent_div = soup.find("div", {"class": "product-tile"})
            # metadata_containers = parent_div.find("div", recursive=False)
            # # print(metadata_containers)
            # name = metadata_containers.find("a", {"class": "name-link"}).text
            # price = metadata_containers.find("span", {"class": "product-sales-price"}).text
            # print(name, price)

            # print("here is p:", p)
            # metadata_divs = print(p.xpath("//div//div[@class='product-tile']"))  # this outputs the contents of the product-tile
            # metadata_divs = p.xpath("//div//div[@class='product-tile']")
            # print(len(metadata_divs), metadata_divs.xpath(product_name_path).extract())
            # name = metadata_divs.xpath()
            
            # x = p.xpath("//div[@class='product-name']/a[@class='name-link']/text()")
            # print(len(x), x.extract())

        # names = selector_lists_of_products.xpath().extract()  # FIXME: is 2304 long, should be 48
        # print("PRINT SPAM", len(names), names[0], len(selector_lists_of_products), selector_lists_of_products[0])
        # prices = selector_lists_of_products.xpath().extract()
        # colors = selector_lists_of_products.xpath().extract()
        # print(names)

        products_from_the_page = []
        # # print("are we here", len(names), len(prices), len(colors))
        # for (name, price, available_colors) in zip(names, prices, colors):
        #     # print(name, price, available_colors)
        #     p = Product(name=name, price=price, colors=available_colors)
        #     # print(p)
        #     products_from_the_page.append(p)

        return products_from_the_page
