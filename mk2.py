from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import time

options = webdriver.ChromeOptions()
options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

data = []

def get_offers_for_model(model_url, model_name, image_url):
    try:
        driver.get(model_url)
        time.sleep(2)

        # Прокрути вниз одразу після відкриття
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        clicks = 0
        max_clicks = 20
        while clicks < max_clicks:
            try:
                more_button = driver.find_element(By.CSS_SELECTOR, ".list-more-div-small")
                if not more_button.is_displayed():
                    break
                driver.execute_script("arguments[0].click();", more_button)
                time.sleep(1.5)
                # прокрутити вниз після підгрузки
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                clicks += 1
            except NoSuchElementException:
                break
        offer_rows = driver.find_elements(By.CSS_SELECTOR, ".where-buy-table tr")
        if not offer_rows:
            print(f"⚠️ Для моделі {model_name} немає пропозицій.")
            return

        for row in offer_rows:
            try:
                shop_element = row.find_element(By.CSS_SELECTOR, ".where-buy-description a.it-shop")
                shop = shop_element.text.strip()
            except:
                shop = "N/A"

            try:
                city_element = row.find_element(By.CSS_SELECTOR, ".where-buy-description .it-deliv")
                city = city_element.text.strip().replace("Доставка:", "").replace("з", "").replace("у", "").strip()
            except:
                city = "N/A"

            try:
                price_element = row.find_element(By.CSS_SELECTOR, ".where-buy-price a")
                price_text = price_element.text.replace("грн.", "").replace("грн", "").replace(" ", "").replace("\u202f", "").strip()
                price = float(price_text.replace(",", ".")) if price_text else 0.0
            except:
                price = 0.0

            if shop != "N/A" and city != "N/A" and price != 0.0:
                data.append({
                    "Model": model_name,
                    "Image URL": image_url,
                    "Shop": shop,
                    "City": city,
                    "Price": price
                })
    except Exception as e:
        print(f"❌ Не вдалося отримати пропозиції для {model_name}: {e}")


# Додає пропозиції зі сторінки докладних пропозицій магазину (shop-120234)
def parse_model_offers_page():
    offer_rows = driver.find_elements(By.CSS_SELECTOR, "tr.shop-120234")
    for row in offer_rows[:7]:
        try:
            image_element = row.find_element(By.CSS_SELECTOR, ".where-buy-img img")
            image_url = image_element.get_attribute("src")
        except:
            image_url = ""

        try:
            shop_element = row.find_element(By.CSS_SELECTOR, ".where-buy-description a.it-shop")
            shop = shop_element.text.strip()
        except:
            shop = "N/A"

        try:
            city_element = row.find_element(By.CSS_SELECTOR, ".where-buy-description .it-deliv")
            city = city_element.text.strip().replace("Доставка:", "").replace("з", "").replace("у", "").strip()
        except:
            city = "N/A"

        try:
            price_element = row.find_element(By.CSS_SELECTOR, ".where-buy-price a")
            price_text = price_element.text.replace("грн.", "").replace("грн", "").replace(" ", "").replace("\u202f", "").strip()
            price = float(price_text.replace(",", ".")) if price_text else 0.0
        except:
            price = 0.0

        data.append({
            "Model": "N/A",
            "Image URL": image_url,
            "Shop": shop,
            "City": city,
            "Price": price
        })

def scrape_ekua_fridges():
    base_url = "https://ek.ua/ua/list/149/"
    models = []


    page = 1
    while page <= 2:
        try:
            url = f"{base_url}{page}/"
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".model-short-div")))
            products = driver.find_elements(By.CSS_SELECTOR, ".model-short-div")

            if not products:
                break

            for product in products:
                try:
                    title_elem = product.find_element(By.CSS_SELECTOR, "a.model-short-title")
                    model_name = title_elem.text.strip()
                    model_url = title_elem.get_attribute("href")

                    try:
                        img_elem = product.find_element(By.CSS_SELECTOR, ".model-short-photo img")
                        img_url = img_elem.get_attribute("src")
                    except:
                        img_url = ""

                    models.append((model_url, model_name, img_url))
                except Exception as e:
                    print(f"❌ Помилка парсингу моделі: {e}")

            print(f"✅ Оброблено сторінку {page}")
            page += 1
        except Exception as e:
            print(f"❌ Помилка завантаження сторінки {page}: {e}")
            break

    for model_url, model_name, img_url in models:
        get_offers_for_model(model_url, model_name, img_url)
        time.sleep(1)

try:
    scrape_ekua_fridges()
finally:
    driver.quit()

df = pd.DataFrame(data)
df.to_csv("ek.csv", index=False, encoding='utf-8-sig')
print("✅ Дані збережено в ek.csv")
