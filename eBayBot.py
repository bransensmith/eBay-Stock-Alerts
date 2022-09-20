import smtplib
import time
from email.message import EmailMessage
from time import sleep

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


def update_on_results(iteration, item_storage_file, title_string, price_string):
    product_emb_link = 's-item__link'
    product_emb_img = 's-item__image-img'

    product_image_href = iteration.find_elements(by=By.CLASS_NAME, value=product_emb_img)

    image_link = str
    for link in product_image_href:
        image_link = link.get_attribute("src")

    product_href = iteration.find_elements(by=By.CLASS_NAME, value=product_emb_link)

    for link in product_href:
        product_link = link.get_attribute("href")
        start_segment = product_link.find('https://www.ebay.com/itm/') + len('https://www.ebay.com/itm/')

        end_segment = str
        if '?epid=' in product_link:
            end_segment = product_link.find('?epid=')

        elif '?hash=' in product_link:
            end_segment = product_link.find('?hash=')

        substring_flag = product_link[start_segment:end_segment]

        if substring_flag not in compare_list:
            with open(item_storage_file, "a") as update:
                update.write(substring_flag + '\n')

            matched_product_details = [product_link, title_string, price_string, image_link]
            for item in matched_product_details:
                products_matched.append(item)
        else:
            continue


def pre_sort_results(driver, min_range, max_range):
    range_filter = ["[aria-label='Minimum Value in $']", "[aria-label='Maximum Value in $']"]

    # apply number per page
    formatted_filter = driver.current_url + '_ipg%3D240&_ipg=240'
    driver.get(formatted_filter)
    sleep(3)

    for filters in filter_to_apply:
        current_filter = f"""[aria-label='{filters}']"""
        filter_type = driver.find_element(by=By.CSS_SELECTOR, value=current_filter)
        filter_type.click()

        # sleep must be > 2 seconds to allow page elements to load.
        sleep(4)

    for counter, filter_range in enumerate(range_filter):

        range_icon = driver.find_element(by=By.CSS_SELECTOR, value=filter_range)
        range_icon.click()

        if counter == 0:
            range_icon.send_keys(min_range)
        else:
            range_icon.send_keys(max_range)

    sleep(2)

    apply_box_filter = "[aria-label='Submit price range']"
    filter_type = driver.find_element(by=By.CSS_SELECTOR, value=apply_box_filter)
    filter_type.click()
    sleep(3)


def email(subject, payload, email_address):
    msg = EmailMessage()
    msg['subject'] = subject

    msg.set_content(payload, subtype='html')
    msg['to'] = email_address
    user = ''
    msg['from'] = user

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    app_password = ''
    server.login(user, app_password)
    server.send_message(msg)

    server.quit()


def html_formatter(results_found, listings_matched, timer):
    results_found = [results_found[i:i + 4] for i in range(0, len(results_found), 4)]
    results_found.sort(key=lambda x: x[2])
    results_found = sum(results_found, [])

    desc_filters = ', '.join(product_description_filters)
    buy_format = ', '.join(filter_to_apply)
    match_filters = ', '.join(weighted_words)

    counter_set = int((len(results_found) / 4))
    html_formatted = ''
    footer = ''

    counter_increment = 0
    for specs in range(0, len(results_found), 4):

        counter_increment += 1

        if counter_increment == counter_set:
            footer = f"""{counter_set} result(s) in: {timer}s"""

        if specs < len(results_found) - 1:
            link_address = (results_found[specs + 0])
            item_name = (results_found[specs + 1])
            item_price = (results_found[specs + 2])
            item_image = (results_found[specs + 3])

            match_percent_str = item_name.lower()
            returned_count_list = [word for word in weighted_words if word in match_percent_str]

            weight_total = int(len(weighted_words))
            match_total = int(len(returned_count_list))
            match_percent = int(round(match_total / weight_total, 2) * 100)

            form_1, form_2 = '', ''

            if match_percent == 100:
                form_1 = '<mark>'
                form_2 = '</mark>'

            href_link = f"""<p style="padding: 5px; border-top:2px solid black;">
                               <img src="{item_image}"><br>
                               {form_1}Product match: {match_percent}% {form_2}<br> <br>
                               {item_name}<br>
                               {item_price}<br>
                               <center> <a href="{link_address}">eBay | Result {counter_increment}</a> <br> 
                               <br> {footer} </center></p>"""

            html_formatted = html_formatted + href_link

    format_html = f"""<!DOCTYPE html>
           <html>
           <body style="background-color:#F2F0EF">
               <h2 style="color:red"> {listings_matched} result(s) found </h2>
               <b> Your search criteria </b> <br>
               Item: {main_product_name} <br>
               Price range: ${min(price_range)} - ${max(price_range)} <br>
               Buying format: {buy_format} <br> <br>
               Product filters: {desc_filters} <br> <br>
               Match words: {match_filters} <br>
               {html_formatted}
           </body>
           """

    return format_html


def measure_selenium_results(item_title):
    if not any(word in item_title for word in
               product_description_filters) and item_title != 'Shop on eBay' and main_product_name in item_title:
        return True


def selenium_main(min_range, max_range, update_file):
    page_navigator = [ebay_item_link]
    page_count = 'pagination__items'
    product_returned = 's-item__pl-on-bottom'
    title_class = 's-item__title'
    price_class = 's-item__price'

    items_found = 0

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=chrome_options)

    start = time.time()

    for pages in page_navigator:
        driver.get(pages)

        # index starts at 0
        if page_navigator.index(pages) == 0:
            sleep(3)

            pre_sort_results(driver, min_range, max_range)

            try:
                pages_found = driver.find_element(by=By.CLASS_NAME, value=page_count)
                element = pages_found.find_elements(by=By.TAG_NAME, value="a")
                sleep(2)

                for counter, page in enumerate(element):

                    if counter >= 1:
                        page_link = page.get_attribute("href")
                        page_navigator.append(page_link)

            except NoSuchElementException:
                pass

        else:
            continue

        results = driver.find_elements(by=By.CLASS_NAME, value=product_returned)
        sleep(1)

        for i in results:
            item_title = i.find_elements(by=By.CLASS_NAME, value=title_class)
            title_string = item_title[0].text

            item_price = i.find_elements(by=By.CLASS_NAME, value=price_class)
            price_string = item_price[0].text

            if measure_selenium_results(title_string):
                items_found += 1

                update_on_results(i, update_file, title_string, price_string)

    end = time.time()
    timer = round((end - start), 2)

    if len(products_matched) != 0:
        email_message = html_formatter(products_matched, items_found, timer)

        if email_message:
            email('eBay Bot', email_message, 'bransen.smith@icloud.com')


if __name__ == '__main__':

    # write found product #s to this file to prevent repeat alerts in future notifications.
    txt_file = ''
    
    # searched product link
    ebay_item_link = 'https://www.ebay.com/sch/i.html?_from=R40&_trksid=p2334524.m570.l1313&_nkw=swatch+x+omega' \
                     '&_sacat=0&LH_TitleDesc=0&_odkw=swatch+X+omega '
    # buying format
    filter_to_apply = ['OMEGA', 'Buy It Now', 'US Only']
    
    # product name
    main_product_name = 'Omega x Swatch'
    
    # filters results if description contains any of these words
    product_description_filters = ['lady', 'ladies', 'woman', 'broken', 'parts', 'used', 'missing', 'damaged',
                                   'pre-owned',
                                   'pink', 'strap', 'box only', 'scratched']
    
    # weighted % to determine match accuracy
    weighted_words = ['omega x swatch', 'moonswatch', 'mission', 'mars', 'bioceramic']


    # base price must remain high to filter unwanted returns
    price_range = [260, 350]
    
    products_matched = []

    with open(txt_file, "r") as lst:
        lines = lst.read().split()

    compare_list = []
    for line in lines:
        compare_list.append(line)

    selenium_main(min(price_range), max(price_range), txt_file)
