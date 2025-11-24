import configparser
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.api.v1.schemas.users import UserBase
from app.models.company import Company
from app.models.team_company import TeamCompany
from utils.extension import get_element_xpath


def format_string(input_str: str) -> str:
    return input_str.replace(" ", "").replace("-", "").replace("_", "").lower()


class ExtensionService:
    def __init__(self, db: Session):
        self.db = db
        filename = "fill-form-config.ini"
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(filename, encoding="utf-8")
        self.matches = config.items("MATCH")
        self.config = config.read(filename, encoding="utf-8")
        self.config_part = config["PART"]

    def input_handler(
        self,
        input_count,
        xpath: str,
        input_type,
        key,
        hiragana_flg,
    ):
        try:
            if input_type == "email":
                result = {
                    "xpath": xpath,
                    "key_name": "mail",
                }
            else:
                result = {
                    "xpath": xpath,
                    "key_name": key,
                }
            return input_count + 1, result
        except Exception as e:
            raise e

    def check_tel_and_postal_code_wrong(self, tel1, tel2, results):
        if any(item["key_name"] == tel1 for item in results) and not any(
            item["key_name"] == tel2 for item in results
        ):
            return True
        else:
            return False

    def fill_form(self, html):
        results = []
        html = re.sub(r"<br\s*\/?>", "", html)
        soup = BeautifulSoup(html, "html.parser")
        dummy_tags = soup.find_all(
            lambda tag: tag.get("class") and "dummy" in " ".join(tag["class"])
        )
        for tag in dummy_tags:
            tag.decompose()
        form = soup.find("form", {"method": "post"})
        if form is None:
            form = soup.find("form")
        input_tags = []
        label_element = []
        elements = []
        if form:
            label_element = []
            input_tags = form.find_all(["input", "textarea"])
            elements = form.find_all()
        hiragana_flg = (self.has_hiragana(html),)

        # get label of tag
        for input in input_tags:
            if input.get("id") is not None:
                input_label = soup.find("label", {"for": input.get("id")})
                if input_label is not None:
                    input_label = input_label.text
                    label_element.append(
                        {
                            "xpath": get_element_xpath(input),
                            "label": input_label,
                        }
                    )

        prev = None
        for element in reversed(elements):
            if (
                element.name == "input"
                and element.get("type") in ["text", "email", "tel", "url"]
            ) or element.name == "textarea":
                xpath_element = get_element_xpath(element)
                is_existing = False
                for l_element in label_element:
                    if l_element.get("xpath") == xpath_element:
                        is_existing = True
                        break
                if is_existing is False:
                    prev = xpath_element
            elif prev:
                text = (
                    element.get_text()
                    .replace(" ", "")
                    .replace("\t", "")
                    .replace("\n", "")
                )
                if len(text) > 0:
                    label_of_matches = False
                    for match in self.matches:
                        values = set((match[1]).split(","))
                        for value in values:
                            if value in text:
                                label_of_matches = True
                                break
                        if label_of_matches is True:
                            break
                    if label_of_matches is True:
                        label_element.append({"xpath": prev, "label": text})
                        prev = None

        # handle Tag
        for input_tag in input_tags:
            input_html = str(input_tag.prettify())
            input_count = 0
            input_type = input_tag.get("type")
            input_name = input_tag.get("name")
            input_id = input_tag.get("id")
            input_maxlength = input_tag.get("maxlength") or ""
            input_placeholder = input_tag.get("placeholder") or ""
            input_class = input_tag.get("class") or ""

            input_maxlength = int(input_maxlength) if input_maxlength != "" else -1
            formatted_input_tag_name = format_string(input_name) if input_name else None
            formatted_input_tag_type = format_string(input_type) if input_type else None
            formatted_input_tag_id = format_string(input_id) if input_id else None
            # check hidden tag
            if (
                "hidden" in input_html
                or "display:none" in input_html
                or "display: none" in input_html
                or "display : none" in input_html
            ):
                continue
            # check untext tag
            if (
                input_type == "submit"
                or input_type == "button"
                or input_type == "radio"
                or input_type == "checkbox"
            ):
                continue
            result = None
            label = ""
            label_regex = ""
            xpath = get_element_xpath(input_tag)
            for element in label_element:
                if xpath == element.get("xpath"):
                    label = element.get("label")
                    pattern = r"[^\w\s()（）]+"
                    label_regex = re.sub(pattern, "", label).strip()
            for match in self.matches:
                key = match[0]
                values = set(format_string(match[1]).split(","))
                # tag map with config
                if input_count == 0 and (
                    formatted_input_tag_name in values
                    or formatted_input_tag_id in values
                    or formatted_input_tag_type in values
                    or (label and label_regex in values)
                ):
                    input_count, result = self.input_handler(
                        input_count, xpath, input_type, key, hiragana_flg
                    )
                if input_count > 0:
                    results.append(result)
                    break
            if result is None:
                for match in self.matches:
                    key = match[0]
                    values = set(format_string(match[1]).split(","))
                    # tag not map with config, use part
                    try:
                        keywords_string = self.config_part.get(key)
                        if not keywords_string:
                            continue
                        for keyword in keywords_string.replace(" ", "").split(","):
                            if (
                                input_count == 0
                                and input_name is not None
                                and (
                                    keyword in input_name
                                    or keyword in input_placeholder
                                    or keyword in input_class
                                    or keyword in input_html
                                )
                            ):
                                input_count, result = self.input_handler(
                                    input_count,
                                    xpath,
                                    input_type,
                                    key,
                                    hiragana_flg,
                                )
                    except Exception as e:
                        raise e
                    if input_count > 0:
                        results.append(result)
                        break
        if self.check_tel_and_postal_code_wrong("tel1", "tel2", results):
            for result in results:
                if result["key_name"] == "tel1":
                    result["key_name"] = "tel"
        if self.check_tel_and_postal_code_wrong("tel2", "tel1", results):
            for result in results:
                if result["key_name"] == "tel":
                    result["key_name"] = "tel1"
        if self.check_tel_and_postal_code_wrong("postalCode1", "postalCode2", results):
            for result in results:
                if result["key_name"] == "postalCode1":
                    result["key_name"] = "postalCode"
        if self.check_tel_and_postal_code_wrong("postalCode2", "postalCode1", results):
            for result in results:
                if result["key_name"] == "postalCode":
                    result["key_name"] = "postalCode1"
        return results

    def search_company(self, company_url: str, current_user: UserBase):
        company_url = urlparse(company_url).netloc
        company = self.db.exec(
            select(Company)
            .where(Company.hp_url == company_url)
            .join(
                TeamCompany,
                Company.corporate_number == TeamCompany.corporate_number,
                isouter=True,
            )
            .where(TeamCompany.team_id == current_user.team_id)
        ).one()
        return company

    def has_hiragana(self, page_source: str):
        return any([x in page_source for x in ("ふりがな", "ひらがな")])
