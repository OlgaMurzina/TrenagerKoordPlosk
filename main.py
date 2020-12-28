import os
import sqlite3
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QListWidget

from design_form import Ui_MainWindow


class MyWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.ans = set()
        self.coord = []
        self.ans = ''  # строка координат, которые ввел пользователь
        self.count_koord = 0  # счетчик координат,которые вввел пользователь
        self.error = 0  # счетчик допущенных ошибок
        self.images = []
        self.count_finish = 0  # счетчик нажатий на кнопку Закончить работу
        self.o = ''  # оценка работы ученика
        # вызов обработчика событий - в нем храним связи сигналы - слоты
        self._connectAction()
        # подключение к БД
        self.db_connection()
        self.change_img()
        self.label_8.setWordWrap(True)
        self.msgBox = QMessageBox()
        self.lstWidget = QListWidget()
        self.fam = None
        self.mess = 'Error!'

    # создание подключения и курсора для работы с БД
    def db_connection(self):
        # создание подключения к БД
        self.con = sqlite3.connect("SQLiteStudio\koord_pl.db")
        # Создание курсора
        self.cur = self.con.cursor()

    # блок событий нажатия разных кнопок
    def _connectAction(self):
        # обработка нажатия кнопки-подтверждения ввода данных ребенка
        self.pushButton_3.clicked.connect(self.ok)
        # вызов обработчика нажатия кнопки Проверить
        self.pushButton.clicked.connect(self.run)
        # обработка нажатия ребенком кнопки Закончить
        self.pushButton_2.clicked.connect(self.finish)
        # работа с меню программы
        self.action_2.triggered.connect(self.addFile)
        self.action_3.triggered.connect(self.delFile)
        self.action_5.triggered.connect(self.viuwer)

    # обработка событий из строки Меню-Файл
    def addFile(self):
        # добавление файла к базе
        fname = QFileDialog.getOpenFileName(None, 'Выбрать картинку по имени файла')[0]
        # Подключение к БД
        try:
            if not fname:
                self.mess = 'Вы не выбрали файл!'
                raise ValueError(self.mess)
            else:
                fname = fname.split("/")[-1]
                name = f"{fname.split('.')[0]}"
                koord = os.path.join('coord', f'{name}.txt')
                fname = os.path.join('images', f'{name}.bmp')
                result = self.cur.execute("""SELECT id, del FROM files
                                           WHERE image = ?""", (f'{name}',)).fetchone()
                # запрос на путь к файлу с координатами
                if not result:
                    if os.path.exists(f'{fname}') and os.path.exists(f'{koord}'):
                        self.cur.execute("""INSERT INTO files(image, name_file, koord_file, del) VALUES (?, ?, ?, 0)""",
                                         (name, fname, koord))
                        self.con.commit()
                        self.change_img()
                        # выдавать во всплывающем окне сообщение о том, что файл успешно добавлен в базу
                        self.msgBox.setText("Файл успешно добавлен в базу данных")
                    else:
                        self.mess = "Рисунок с таким именем не подходит для нашей программы :("
                        raise ValueError(self.mess)
                else:
                    if result[1] == 1:
                        self.cur.execute("""UPDATE files SET del = ? WHERE id = ?""",
                                         (0, result[0]))
                        self.con.commit()
                        self.change_img()
                        # выдавать во всплывающем окне сообщение о том, что файл успешно добавлен в базу
                        self.msgBox.setText("Файл успешно добавлен в базу данных")
                    else:
                        self.msgBox.setText("Этот файл уже есть в базе данных")
                self.msgBox.setWindowTitle("Добавление файла")
                self.msgBox.exec()
        except ValueError as e:
            self.err()

    def delFile(self):
        # удаление записи о рисунке из БД
        self.lstWidget = QListWidget()
        self.lstWidget.addItems(self.images)
        self.lstWidget.itemClicked.connect(self._on_item_clicked)
        self.lstWidget.show()

    def _on_item_clicked(self, item):
        # обработка выбора файла на удаление и пометка файла в базе флажком
        self.cur.execute("""UPDATE files SET del = ? WHERE image = ?""", (1, item.text()))
        self.con.commit()
        self.msgBox.setText("Файл удален из базы данных")
        self.msgBox.setWindowTitle("Удаление файла")
        self.msgBox.exec()
        self.change_img()

    def viuwer(self):
        # просмотр результатов учеников - выгрузка ФИ, кол-ва тренировок и средней оценки из БД
        result = self.cur.execute("""SELECT familia, name, count, average_mark FROM childrens""").fetchall()
        text = 'Фамилия Имя Вход Оценка\n'
        for x in result:
            text += x[0] + ' ' + x[1] + '   ' + str(x[2]) + '   ' + str(x[3]) + '\n'
        self.msgBox.setWindowTitle("Ответ на запрос:")
        # self.msgBox.resize(200, 200)
        self.msgBox.setText(text)
        self.msgBox.exec()

    def change_img(self):
        # блок выбора рисунка из выпадающего списка, сформированного по БД
        self.images = list(
            map(lambda x: x[0], self.cur.execute("""SELECT image FROM files WHERE del = 0 """).fetchall()))
        self.comboBox.addItems(self.images)
        # вызов загрузки стартового рисунка - первого в списке комбобокса
        self.select_task(self.images[0])
        # вызов обработчика выбора названия рисунка в комбобоксе
        self.comboBox.activated.connect(self.select_task)

    def run(self):
        # проверка наличия такого кортежа в файле рисунка и вердиткт - есть или нет
        # сообщения об ошибках
        try:
            # ввод координаты Х
            self.x = self.lineEdit_2.text()
            # ввод координаты Y
            self.y = self.lineEdit.text()
            # сравнение координат с координатами из файла к выбранному рисунку
            koord = str(self.x) + ';' + str(self.y)
            if not self.x or not self.y or not self.coord:
                raise ValueError()
            # выставление оценки, если все координаты введены или сообщение о коорректоности ответа

            elif koord in self.coord:
                self.count_koord += 1
                self.ans += '(' + str(koord) + ') '
                self.label_8.setText(f"OK {koord}")
                self.label_9.setWordWrap(True)
                self.label_9.setText(f"{self.ans}")
                # удаление кортежа из set, чтобы понимать, совершен ли полный обход
                self.coord.remove(koord)
            else:
                # обработка неверного ответа
                if str(koord) in self.ans:
                    self.label_8.setText("Повтор координат.\nБерите следующую точку.")
                else:
                    self.label_8.setText("Неверно.\nПопробуйте еще раз.")
                    self.error += 1
            self.lineEdit_2.setText('')
            self.lineEdit.setText('')
        except ValueError:
            self.label_8.setText("Нажмите кнопку\nЗакончить работу")

    def mark(self):
        # Выставление оценки ученику
        try:
            if not self.count_koord:
                self.mess = "Работа не начата. Оценить невозможно!"
                raise ValueError(self.mess)
            oc = (self.count_koord - self.error) / self.count_koord
            if oc > 0:
                if oc > 0.85:
                    self.o = '5'
                elif oc > 0.67:
                    self.o = '4'
                elif oc > 0.5:
                    self.o = '3'
                else:
                    self.o = 'Неплохо,\nно нужно еще поработать с теорией'
            else:
                self.o = 'Плохо,\nнужно еще поработать с теорией'
            t = f"Работа завершена успешно! Ошибок - {self.error} Оценка - {self.o} Нажмите кнопку 'Закончить работу'"
            self.msgBox.setWindowTitle("Завершение работы")
            self.msgBox.setText(f'{t}')
            self.msgBox.exec()
        except ValueError:
            self.err()

    def finish(self):
        # нажатие кнопки Закончить работу с учетом повторного нажатия
        # в идеале - диалоговое окно про все равно закончить
        self.count_finish += 1
        self.msgBox.setWindowTitle("Завершение работы")
        t = 'Спасибо за работу! Нажмите "Закончить работу"'
        if not self.fam:
            t = "Нет данных: введите свою фамилию и имя!"
            self.msgBox.setWindowTitle("Данные ребенка")
            self.count_finish = 0
        elif self.count_koord == 0 and self.count_finish == 1:
            t = "Работа не началась. Чтобы выйти из программы, нажмите 'Ok'.Чтобы продолжить, нажмите 'Cancel'"
            self.msgBox.setWindowTitle("Завершение работы")
            self.msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            self.msgBox.buttonClicked.connect(self.msgbtn)
        elif self.coord and self.count_finish == 1:
            self.count_finish = 0
            t = "Вы не закончили уражнение. Чтобы выйти из программы, нажмите 'Ok'.Чтобы продолжить, нажмите 'Cancel'"
            self.msgBox.setWindowTitle("Завершение работы")
            self.msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            self.msgBox.buttonClicked.connect(self.msgbtn)
        elif not self.coord and self.count_finish == 1:
            # Выставление оценки
            self.mark()
            # Выполнение запроса и получение всех результатов
            res = self.cur.execute("""SELECT ID, count FROM childrens WHERE familia = ? and name = ?""",
                                   (self.fam, self.name)).fetchall()
            # запись результатов в таблицу
            if not res:
                # У нового ребенка не была нажата кнопка ОК в начале работы
                self.ok()
            # внесение изменений в БД по ученику после работы
            id_im = self.cur.execute("""SELECT ID FROM files WHERE image = ?""",
                                     (self.comboBox.currentText(),)).fetchone()
            n = self.cur.execute("""SELECT count, average_mark FROM childrens WHERE familia = ? and name = ?""",
                                 (self.fam, self.name)).fetchone()
            n = list(n)
            if not n[1]:
                n[1] = self.o
            # обновление записи об ученике в БД
            self.cur.execute(
                """UPDATE childrens SET count = ?, images = ?, average_mark = ? WHERE familia = ? and name = ?""",
                (n[0] + 1, id_im[0], str((float(n[1]) + float(self.o)) / 2), self.fam, self.name))
            self.con.commit()
            t = 'Данные о работе успешно внесены в базу данных!'
            self.msgBox.setWindowTitle("Завершение работы")
            self.msgBox.setIcon(QMessageBox.Information)
            self.msgBox.setText(f'{t}')
            self.msgBox.exec()
            sys.exit(app.exec_())
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setText(f'{t}')
        self.msgBox.exec()

    def msgbtn(self, i):
        # обработка кнопки выхода из программы - ОК и Cancel
        if i.text() == 'OK':
            sys.exit(app.exec_())
        else:
            self.count_finish = 0

    def select_task(self, text):
        # работа с базой рисунков - определение пути к файлу из БД
        # Подключение к БД
        # запрос на путь к файлу с рисунком
        result = self.cur.execute("""SELECT name_file FROM files
                                WHERE image = ?""", (self.comboBox.currentText(),)).fetchone()[0]
        # запрос на путь к файлу с координатами
        result_1 = self.cur.execute("""SELECT koord_file FROM files
                                WHERE image = ?""", (self.comboBox.currentText(),)).fetchone()[0]
        # открытие графического файла по выбранному рисунку
        self.pixmap = QPixmap(f'{result}')
        # увеличение размера до размера экрана
        self.label_7.move(85, 0)
        size_window = self.label_7.size()
        self.label_7.setMaximumSize(size_window)
        # Отображаем содержимое QPixmap в объек)те QLabel по размерам окна
        self.label_7.setPixmap(QPixmap(self.pixmap.scaled(self.label_7.size(), Qt.KeepAspectRatio)))
        # связь рисунка с файлом из базы рисунков: название рисунка - ID - имя файла с координатами

        # проверка на существование файла с координатами к рисунку!!!!!
        # если рисунок есть, а координат нет, то удалять рисунок из базы!!!!
        self.coord = open(f'{result_1}', 'r').read().split('\n')
        self.coord = set([a.strip('#') for a in self.coord])
        if '' in self.coord:
            self.coord.remove('')
        self.ans = ''

    def err(self):
        #
        self.msgBox.setIcon(QMessageBox.Warning)
        self.msgBox.setWindowTitle("Ошибка!")
        self.msgBox.setText(f'{self.mess}')
        self.msgBox.exec()

    def ok(self):
        # ввод фамилии ребенка
        self.fam = self.lineEdit_3.text()
        # ввод имени ребенка
        self.name = self.lineEdit_4.text()
        # проверка корректности ввода фамилии и имени
        try:
            if not self.fam and self.name:
                self.mess = 'Не введены фамилия и имя ребенка!'
                raise ValueError(self.mess)
            elif not self.fam:
                self.mess = 'Не введена фамилия ребенка!'
                raise ValueError(self.mess)
            elif not self.name:
                self.mess = 'Не введено имя ребенка!'
                raise ValueError(self.mess)
            elif not self.fam.isalpha() and not self.name.isalpha():
                self.mess = 'Ошибка при вводе имени и фамилии: присутствуют посторонние символы!'
                raise ValueError(self.mess)
            elif self.fam.isalpha() and not self.name.isalpha():
                self.mess = 'Ошибка при вводе имени: присутствуют посторонние символы!'
                raise ValueError(self.mess)
            elif self.name.isalpha() and not self.fam.isalpha():
                self.mess = 'Ошибка при вводе фамилии: присутствуют посторонние символы!'
                raise ValueError(self.mess)
            else:
                # поиск ребенка по базе - если есть, то фиксируем ID, если нет, то добавляем в базу новый ID и данные
                # Выполнение запроса и получение всех результатов
                res = self.cur.execute("""SELECT ID FROM childrens WHERE familia = ? and name = ?""",
                                       (self.fam, self.name)).fetchall()
                if not res:
                    self.con.execute(
                        """INSERT INTO childrens(familia, name) VALUES (?, ?)""",
                        (self.fam, self.name))
                    self.mess = 'Фамилия и имя успешно внесены в базу данных!'
                else:
                    self.mess = 'Фамилия и имя уже есть в базе данных :)'
                self.con.commit()
            self.msgBox.setIcon(QMessageBox.Information)
            self.msgBox.setWindowTitle("Ввод данных")
            self.msgBox.setText(f'{self.mess}')
            self.msgBox.exec()
        except ValueError:
            self.err()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.excepthook = except_hook
sys.exit(app.exec_())
