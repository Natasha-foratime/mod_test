import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# Настройки
URL = "http://localhost:8081"
LOGIN = "standard_user"
PASSWORD = "secret_sauce"

@pytest.fixture()
def driver():
    # Настройки для Chrome: отключаем автоперевод, чтобы он не менял текст на странице
    options = webdriver.ChromeOptions()
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    
    # Неявное ожидание (10 секунд) — если элемента нет, Selenium будет ждать его до 10 сек.
    driver.implicitly_wait(10) 
    yield driver
    driver.quit()

def login(driver):
    """Вспомогательная функция для входа"""
    driver.get(URL)
    driver.find_element(By.ID, "user-name").send_keys(LOGIN)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "login-button").click()
    # Ждем, пока загрузится страница товаров
    WebDriverWait(driver, 5).until(EC.url_contains("inventory.html"))

# --- ТЕСТ 1: Успешный вход ---
def test_01_successful_login(driver):
    login(driver)
    assert "inventory.html" in driver.current_url
    title_text = driver.find_element(By.CLASS_NAME, "title").text
    # Приводим к нижнему регистру, чтобы не зависеть от капса
    assert title_text.lower() == "products"

# --- ТЕСТ 2: Неверный пароль ---
def test_02_invalid_password(driver):
    driver.get(URL)
    driver.find_element(By.ID, "user-name").send_keys(LOGIN)
    driver.find_element(By.ID, "password").send_keys("wrong_password")
    driver.find_element(By.ID, "login-button").click()
    error = driver.find_element(By.CSS_SELECTOR, "h3[data-test='error']").text
    assert "Username and password do not match" in error

# --- ТЕСТ 3: Пустое поле логина ---
def test_03_empty_username(driver):
    driver.get(URL)
    driver.find_element(By.ID, "login-button").click()
    error = driver.find_element(By.CSS_SELECTOR, "h3[data-test='error']").text
    assert "Username is required" in error

# --- ТЕСТ 4: Добавление товара в корзину ---
def test_04_add_to_cart(driver):
    login(driver)
    driver.find_element(By.ID, "add-to-cart-sauce-labs-backpack").click()
    
    # Ждем, пока появится значок с цифрой 1
    cart_badge = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
    )
    assert cart_badge.text == "1"

# --- ТЕСТ 5: Удаление товара из корзины ---
def test_05_remove_from_cart(driver):
    login(driver)
    driver.find_element(By.ID, "add-to-cart-sauce-labs-backpack").click()
    driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
    
    # Ждем появления кнопки "Удалить" и кликаем
    remove_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "remove-sauce-labs-backpack"))
    )
    remove_btn.click()
    
    # Ждем, пока значок с количеством товаров исчезнет
    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
    )

# --- ТЕСТ 6: Сортировка товаров по цене (от низкой к высокой) ---
def test_06_sort_by_price_low_to_high(driver):
    login(driver)
    select_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "product_sort_container"))
    )
    select = Select(select_element)
    select.select_by_value("lohi")
    
    prices = driver.find_elements(By.CLASS_NAME, "inventory_item_price")
    first_price = float(prices[0].text.replace("$", ""))
    second_price = float(prices[1].text.replace("$", ""))
    assert first_price <= second_price

# --- ТЕСТ 7: Переход в корзину ---
def test_07_go_to_cart(driver):
    login(driver)
    driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
    
    # Ждем, пока в URL появится 'cart.html'
    WebDriverWait(driver, 5).until(EC.url_contains("cart.html"))
    
    title_text = driver.find_element(By.CLASS_NAME, "title").text
    # Приводим к нижнему регистру
    assert title_text.lower() == "your cart"

# --- ТЕСТ 8: Проверка заголовка страницы ---
def test_08_page_title(driver):
    driver.get(URL)
    assert "Swag Labs" in driver.title

# --- ТЕСТ 9: Выход из системы (Logout) ---
def test_09_logout(driver):
    login(driver)
    driver.find_element(By.ID, "react-burger-menu-btn").click()
    
    # Ждем появления кнопки выхода и кликаем
    logout_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "logout_sidebar_link"))
    )
    logout_btn.click()
    
    # Ждем появления кнопки логина (значит, вышли)
    login_btn = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "login-button"))
    )
    assert login_btn.is_displayed()

# --- ТЕСТ 10: Проверка описания товара ---
def test_10_check_item_description(driver):
    login(driver)
    driver.find_element(By.ID, "item_4_title_link").click()
    
    # Ждем загрузки страницы товара
    WebDriverWait(driver, 5).until(EC.url_contains("inventory-item.html"))
    
    desc = driver.find_element(By.CLASS_NAME, "inventory_details_desc").text
    assert len(desc) > 10 # Проверяем, что описание не пустое