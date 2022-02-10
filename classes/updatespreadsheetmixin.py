import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pyinputplus as pyip
from termcolor import colored
import os
import sys


import classes.budget
import time


# Global Variables for Google API
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]
CREDS = Credentials.from_service_account_file('creds.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('personal-budget')

# Global Variables for app processes
MONTH_NOW = datetime.now().strftime('%B')
MONTHS = ['January', 'February', 'March', 'April', 'May',
          'June', 'July', 'August', 'September', 'October',
          'November', 'December']


class UpdateSpreadsheetMixin:
    """
    Mixin for functions related to spreadsheet operations.
    """

    def color_worksheet_names(self, worksheet):
        """
        Color and capitalize worksheet names.
        """

        if worksheet == 'wants':
            name_worksheet = colored(worksheet.capitalize(), "green")
        elif worksheet == 'needs':
            name_worksheet = colored(worksheet.capitalize(), "red")

        return name_worksheet

    def update_worksheet_cell(self, worksheet, value, row, column):
        """
        Updates Google Sheet worksheet based on present month,
        value and column arguments.
        """
        self.clear_display()
        print(f"Updating {column} in worksheet...\n")
        time.sleep(3)
        month_cell = SHEET.worksheet(worksheet).find(row)
        month_income = SHEET.worksheet(worksheet).find(column)
        SHEET.worksheet(worksheet).update_cell(month_cell.row,
                                               month_income.col, value)
        print(f"{column.title()} updated successfully!\n\n")
        time.sleep(3)

    def input_values_for_worksheet(self, worksheet, month, value):
        """
        Return user input for individual categories.
        """
        self.clear_display()
        month_cell = SHEET.worksheet(worksheet).find(month)
        spendings = {}
        for item in self.categories_list:
            if item != 'TOTAL' and item != 'SURPLUS':
                self.clear_display()

                if worksheet == 'needs':
                    name_item = colored(item, "red")
                elif worksheet == 'wants':
                    name_item = colored(item, "green")

                print(f"Your {self.color_worksheet_names(worksheet)} "
                      f"value for the {month} is: {value}")
                spendings[item] = pyip.inputFloat(
                                                  prompt=f"\nEnter value "
                                                  f"for {name_item}: \n"
                                                 )
                value -= spendings[item]
            else:
                if item == 'TOTAL':
                    spendings[item] = sum(spendings.values())
                elif item == 'SURPLUS':
                    spendings[item] = self.money - spendings['TOTAL']
        self.clear_display()
        print(f"\nUpdating {self.color_worksheet_names(worksheet)} "
               "worksheet with passed values...")
        time.sleep(3)
        for key, value in spendings.items():
            if key != 'SURPLUS':
                key_location = SHEET.worksheet(worksheet).find(key)
                SHEET.worksheet(worksheet).update_cell(month_cell.row,
                                                       key_location.col, value)
        print(f"\n{self.color_worksheet_names(worksheet)} "
               "worksheet updated successfully!")
        time.sleep(3)
        print(f"\nYour summarize costs for "
              f"{self.color_worksheet_names(worksheet)} "
              f"is: {spendings['TOTAL']}")
        time.sleep(5)

        return spendings

    def clear_row(self, worksheet, month):
        """
        Function to clear cells for the selected month and worksheet.
        """
        self.clear_display()
        month_cell = SHEET.worksheet(worksheet).find(month)
        print(f"\nClearing {month} row in "
              f"{self.color_worksheet_names(worksheet)} worksheet...")
        time.sleep(3)
        SHEET.worksheet(worksheet).batch_clear(
            [f"{month_cell.row}:{month_cell.row}"])

        SHEET.worksheet(worksheet).update_cell(
            month_cell.row, month_cell.col, month)
        print(f"\n{month.capitalize()} row in "
              f"{self.color_worksheet_names(worksheet)} "
               "worksheet is now clear.")
        time.sleep(3)
        self.clear_display()

    def clear_worksheet(self, worksheet):
        """
        Clears entire worksheet and populates first column
        with previously catched values.
        """
        self.clear_display()
        print(f"Erasing {self.color_worksheet_names(worksheet)} "
               "worksheet...\n")
        time.sleep(3)
        get_all_values = SHEET.worksheet('needs').get_all_values()
        SHEET.worksheet(worksheet).clear()
        row_values = []
        for li in get_all_values:
            li_li = []
            li_li.append(li[0])
            row_values.append(li_li)

        SHEET.worksheet(worksheet).insert_rows(row_values)
        print(f"{self.color_worksheet_names(worksheet)} "
               "worksheet is now empty.\n")
        time.sleep(3)

    def update_worksheet_categories(self, categories, worksheet, cell):
        """
        Updates worksheet with categories of user's choice.
        """
        self.clear_display()
        print(f"\nUpdating {self.color_worksheet_names(worksheet)} "
               "worksheet...")
        time.sleep(3)
        split_categories = categories.split(',')
        month = SHEET.worksheet(worksheet).find(cell)
        for num, item in enumerate(split_categories):
            if item != 'SURPLUS':
                SHEET.worksheet(worksheet).update_cell(month.row, num+2, item)
        print(f"\n{self.color_worksheet_names(worksheet)} "
               "worksheet updated successfully!")
        time.sleep(3)
        return split_categories

    def create_categories(self, worksheet, default_cat):
        """
        Gets user input to create peronsalized categories or
        use default option. Validates inputs.
        """
        flow = True
        while flow:
            self.clear_display()
            options_menu = pyip.inputMenu(
                ['Default Categories',
                 'Customize Categories',
                 'Get Categories from Spreadsheet',
                 'Back to Main Menu'],
                prompt=f"Select how do you want to manage your "
                f"{self.color_worksheet_names(worksheet)}:\n",
                numbered=True)
            if options_menu == 'Default Categories' or \
               options_menu == 'Customize Categories':
                print(f"\n{options_menu} will delete all "
                       "values in the worksheet.")
                continue_bool = pyip.inputYesNo("\nDo you want to continue? "
                                                "Type Yes or No:\n")
                if continue_bool.lower() == 'yes':
                    self.clear_worksheet(worksheet)
                    if options_menu == 'Customize Categories':
                        user_categories = ''
                        while True:
                            self.clear_display()
                            print("\nEnter your categories WITHOUT "
                                  "whitespaces such as spaces or tabs, "
                                  "DO NOT use commas (,).")
                            print("For enhanced UX, "
                                  "limit yourself to one word entries.")
                            print("\nExample: Vehicle")
                            user_choice = pyip.inputStr(
                                prompt="\nEnter your category and hit Enter."
                                       "\nIf you finish, press 'q' "
                                       "and hit Enter:\n",
                                blockRegexes=[r'\s|,+'])
                            if user_choice.lower() == 'q' and \
                               user_categories != '':
                                user_categories = user_categories[:-1]
                                flow = False
                                break
                            elif (user_choice.lower() == 'q' and
                                  user_categories == ''):
                                print("\nYou did not enter "
                                      "any category! Try again.")
                                time.sleep(5)
                            else:
                                user_categories += (
                                    user_choice.capitalize() + ',')
                    else:
                        user_categories = default_cat
                        flow = False

                else:
                    continue
            elif options_menu == 'Get Categories from Spreadsheet':
                all_values = SHEET.worksheet(worksheet).get_all_values()
                get_categories = all_values[0][1:]
                categories_string = ''
                for item in get_categories:
                    if item != '' and item != 'TOTAL':
                        categories_string += (item + ',')
                user_categories = categories_string[:-1]
                if user_categories == '':
                    print(f"\nYour categories are empty. "
                           "Use Default or customize "
                          f"{self.color_worksheet_names(worksheet)} "
                           "categories yourself.")
                    time.sleep(5)
                    flow = True
                else:
                    flow = False
            else:
                os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

        return user_categories + ',TOTAL' + ',SURPLUS'
