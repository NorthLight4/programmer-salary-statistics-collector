import os
import requests
import time
from datetime import date, timedelta
from dotenv import load_dotenv
from terminaltables import SingleTable


def predict_rub_salary_hh(vacancy):
    if not vacancy['salary'] or vacancy['salary']['currency'] != 'RUR':
        return None

    salary_to = vacancy['salary']['to']
    salary_from = vacancy['salary']['from']

    if not salary_to:
        avg_salary = salary_from * 1.2
    elif not salary_from:
        avg_salary = salary_to * 0.8
    else:
        avg_salary = (salary_from + salary_to) / 2

    return avg_salary


def predict_rub_salary_sj(vacancy):
    salary_to = vacancy['payment_from']
    salary_from = vacancy['payment_to']

    if salary_to == salary_from == 0:
        return None

    if salary_to == 0:
        avg_salary = salary_from * 1.2
    elif salary_from == 0:
        avg_salary = salary_to * 0.8
    else:
        avg_salary = (salary_from + salary_to) / 2

    return avg_salary


def find_statistics_vacancies_programmer_hh(town_id, date_from):
    api_url = 'https://api.hh.ru/vacancies'
    programming_languages = ['JavaScript', 'Python', 'TypeScript', 'Java', 'C#',
                             'C++', 'C', 'PHP', 'Go', 'Rust', 'Kotlin', 'Swift']
    jobs_info = {}

    for programming_language in programming_languages:
        jobs_info[programming_language] = {}
        predicted_salary, vacancies_processed = 0, 0

        page, pages_number = 0, 1
        while page < pages_number:
            try:
                payload = {
                    'text': f'Программист {programming_language}',
                    'area': town_id,
                    'date_from': date_from,
                    'page': page
                }
                page_response = requests.get(api_url, params=payload)
                page_response.raise_for_status()

                page_data = page_response.json()
                pages_number = page_data['pages']
                page += 1

                predicted_salary_per_page = [predict_rub_salary_hh(vacancy) for vacancy in page_data['items']
                                             if predict_rub_salary_hh(vacancy)]
                predicted_salary += sum(predicted_salary_per_page)
                vacancies_processed += len(predicted_salary_per_page)
            except requests.exceptions.HTTPError:
                time.sleep(1)
            else:
                vacancies_found = page_data['found']
                jobs_info[programming_language]['vacancies_found'] = vacancies_found

        jobs_info[programming_language]['vacancies_processed'] = vacancies_processed
        average_salary = int(predicted_salary / vacancies_processed) if vacancies_processed > 0 else 0
        jobs_info[programming_language]['average_salary'] = average_salary

    return jobs_info


def find_statistics_vacancies_programmer_sj(api_app_key, town_id):
    api_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': api_app_key
    }
    programming_languages = ['JavaScript', 'Python', 'TypeScript', 'Java', 'C#',
                             'C++', 'C', 'PHP', 'Go', 'Rust', 'Kotlin', 'Swift']
    jobs_info = {}

    for programming_language in programming_languages:
        jobs_info[programming_language] = {}
        predicted_salary, vacancies_processed = 0, 0

        page, pages_number = 0, 1
        while page < pages_number:
            try:
                payload = {
                    'catalogues': 48,
                    'town': town_id,
                    'keyword': programming_language,
                    'page': page,
                    'count': 40
                }
                page_response = requests.get(api_url, headers=headers, params=payload)
                page_response.raise_for_status()

                page_data = page_response.json()
                page += 1
                pages_number = page_data['total'] // 40 + (1 if page_data['total'] % 40 else 0)

                predicted_salary_per_page = [predict_rub_salary_sj(vacancy) for vacancy in page_data['objects']
                                             if predict_rub_salary_sj(vacancy)]
                predicted_salary += sum(predicted_salary_per_page)
                vacancies_processed += len(predicted_salary_per_page)
            except requests.exceptions.HTTPError:
                time.sleep(1)
            else:
                vacancies_found = page_data['total']
                jobs_info[programming_language]['vacancies_found'] = vacancies_found

        jobs_info[programming_language]['vacancies_processed'] = vacancies_processed
        average_salary = int(predicted_salary / vacancies_processed) if vacancies_processed > 0 else 0
        jobs_info[programming_language]['average_salary'] = average_salary

    return jobs_info


def create_jobs_table(jobs_info, title):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for language, lang_info in jobs_info.items():
        table_data.append([language] + list(lang_info.values()))
    jobs_table = SingleTable(table_data, title)
    print(jobs_table.table)
    print()


def main():
    load_dotenv()

    one_month_ago = date.today() - timedelta(days=30)
    jobs_info_hh = find_statistics_vacancies_programmer_hh(1, one_month_ago)
    create_jobs_table(jobs_info_hh, 'HeadHunter Moscow')

    sj_api_app_key = os.environ['SJ_API_APP_KEY']
    jobs_info_sj = find_statistics_vacancies_programmer_sj(sj_api_app_key, 4)
    create_jobs_table(jobs_info_sj, 'SuperJob Moscow')


if __name__ == "__main__":
    main()
