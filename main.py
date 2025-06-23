import os
import requests
import time
from datetime import date, timedelta
from dotenv import load_dotenv
from terminaltables import SingleTable


def calculate_avg_salary(salary_from, salary_to):
    if not salary_to:
        return salary_from * 1.2
    elif not salary_from:
        return salary_to * 0.8
    else:
        return (salary_from + salary_to) / 2


def predict_rub_salary_hh(salary_from, salary_to, currency):
    if currency != 'RUR':
        return None

    avg_salary = calculate_avg_salary(salary_from, salary_to)

    return avg_salary


def predict_rub_salary_sj(payment_from, payment_to):
    if payment_from == 0 and payment_to == 0:
        return None

    avg_salary = calculate_avg_salary(payment_from, payment_to)

    return avg_salary


def find_statistics_vacancy_programmer_hh(programming_languages, town_id, date_from):
    api_url = 'https://api.hh.ru/vacancies'
    jobs_stats = {}

    for programming_language in programming_languages:
        predicted_salary, vacancies_processed, vacancies_found = 0, 0, 0

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
            except requests.exceptions.HTTPError:
                time.sleep(1)
            else:
                vacancies_page = page_response.json()
                pages_number = vacancies_page['pages']
                page += 1

                predicted_salaries_per_page = []
                for vacancy in vacancies_page['items']:
                    if vacancy.get('salary'):
                        salary = predict_rub_salary_hh(vacancy['salary']['from'], vacancy['salary']['to'],
                                                       vacancy['salary']['currency'])
                        if salary:
                            predicted_salaries_per_page.append(salary)

                predicted_salary += sum(predicted_salaries_per_page)
                vacancies_processed += len(predicted_salaries_per_page)
                vacancies_found = vacancies_page['found']

        average_salary = int(predicted_salary / vacancies_processed) if vacancies_processed else 0

        jobs_stats[programming_language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }

    return jobs_stats


def find_statistics_vacancy_programmer_sj(api_app_key, programming_languages, town_id):
    api_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': api_app_key
    }
    jobs_stats = {}

    for programming_language in programming_languages:
        predicted_salary, vacancies_processed = 0, 0

        vacancies_per_page = 40
        programmer_vacancy_catalogue_id = 48

        page = 0
        while True:
            try:
                payload = {
                    'catalogues': programmer_vacancy_catalogue_id,
                    'town': town_id,
                    'keyword': programming_language,
                    'page': page,
                    'count': vacancies_per_page
                }
                page_response = requests.get(api_url, headers=headers, params=payload)
                page_response.raise_for_status()
            except requests.exceptions.HTTPError:
                time.sleep(1)
            else:
                vacancies_page = page_response.json()

                predicted_salaries_per_page = []
                for vacancy in vacancies_page['objects']:
                    salary = predict_rub_salary_sj(vacancy['payment_from'], vacancy['payment_to'])
                    if salary:
                        predicted_salaries_per_page.append(salary)

                predicted_salary += sum(predicted_salaries_per_page)
                vacancies_processed += len(predicted_salaries_per_page)
                vacancies_found = vacancies_page['total']

                page += 1
                if not vacancies_page['more']:
                    break

        average_salary = int(predicted_salary / vacancies_processed) if vacancies_processed else 0

        jobs_stats[programming_language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }

    return jobs_stats


def create_jobs_table(jobs_stats, title):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for language, lang_stats in jobs_stats.items():
        table_data.append([language] + list(lang_stats.values()))
    jobs_table = SingleTable(table_data, title)
    return jobs_table.table


def main():
    load_dotenv()

    programming_languages = ['JavaScript', 'Python', 'TypeScript', 'Java', 'C#',
                             'C++', 'C', 'PHP', 'Go', 'Rust', 'Kotlin', 'Swift']

    one_month_ago = date.today() - timedelta(days=30)
    hh_moscow_town_id = 1
    hh_jobs_stats_programmer = find_statistics_vacancy_programmer_hh(programming_languages, hh_moscow_town_id,
                                                                     one_month_ago)
    print(create_jobs_table(hh_jobs_stats_programmer, 'HeadHunter Moscow'))
    print()

    sj_api_app_key = os.environ['SJ_API_APP_KEY']
    sj_moscow_town_id = 4
    sj_jobs_stats_programmer = find_statistics_vacancy_programmer_sj(sj_api_app_key, programming_languages,
                                                                     sj_moscow_town_id)
    print(create_jobs_table(sj_jobs_stats_programmer, 'SuperJob Moscow'))


if __name__ == "__main__":
    main()
