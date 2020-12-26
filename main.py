import os
import sqlite3
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog

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

    # обработка событий из строки Меню-Файл
    def addFile(self):
        # добавление файла к базе
        fname = QFileDialog.getOpenFileName(self, 'Выбрать картинку по имени файла', '')[0]
        # Подключение к БД
        fname = fname.split("/")[-1]
        name = f"{fname.split('.')[0]}"
        koord = os.path.join('coord', f'{name}.txt')
        fname = os.path.join('images', f'{name}.bmp')
        print(name, fname, koord)
        result = self.cur.execute("""SELECT id FROM files
                                   WHERE image = ?""", (f'{name}',)).fetchone()
        # запрос на путь к файлу с координатами
        print(result)
        if not result:
            self.cur.execute("""INSERT INTO files(image, name_file, koord_file) VALUES (?, ?, ?)""",
                             (name, fname, koord))
            self.con.commit()
            self.change_img()
            # выдавать во всплывающем окне сообщение о том, что файл успешно добавлен в базу
            self.label_8.setText('Файл успешно добавлен в базу данных')
        else:
            self.label_8.setText('В базе данных уже есть такой файл')

    def delFile(self):
        # удаление записи о рисунке из БД
        pass

    def viuwer(self):
        # просмотр результатов учеников - выгрузка ФИ, кол-ва тренировок и средней оценки из БД
        pass

    def change_img(self):
        # блок выбора рисунка из выпадающего списка, сформированного по БД
        self.images = list(
            map(lambda x: x[0], self.cur.execute("""SELECT image FROM files WHERE ID > 0 """).fetchall()))
        print(self.images)
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
            print(koord, self.coord)
            if not self.x or not self.y or not self.coord:
                raise ValueError()
            # выставление оценки, если все координаты введены или сообщение о коорректоности ответа

            elif koord in self.coord:
                self.count_koord += 1
                self.ans += '(' + str(koord) + ') '
                print(self.ans)
                self.label_8.setText(f"OK {koord}")
                self.label_9.setWordWrap(True)
                self.label_9.setText(f"{self.ans}")
                self.coord.remove(koord)
                # внесение кортежа в set по координатам файла, чтобы понимать, совершен ли полный обход
                print(self.coord)
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
        print('Жду оценку', 'err', self.error, 'koord', self.count_koord)
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
        print(self.o)

        # self.label_8.setWordWrap(True)
        self.label_8.setText(
            f"Работа завершена успешно! Ошибок - {self.error} Оценка - {self.o} Нажмите еще раз кнопку 'Закончить работу'")

    def finish(self):
        # нажатие кнопки Закончить работу с учетом повторного нажатия
        # в идеале - диалоговое окно про все равно закончить
        self.count_finish += 1
        if self.coord and self.count_finish == 1:
            self.label_8.setWordWrap(True)
            self.label_8.setText(
                "Вы не закончили уражнение. При повторном нажатии на кнопку 'Закончить работу' данные будут потеряны.")
        elif not self.coord and self.count_finish == 1:
            # Выставление оценки
            self.mark()
        else:
            # Выполнение запроса и получение всех результатов
            res = self.cur.execute("""SELECT ID, count FROM childrens WHERE familia = ? and name = ?""",
                                   (self.fam, self.name)).fetchall()
            # запись результатов в таблицу
            if not res:
                # У нового ребенка не была нажата кнопка ОК в начале работы
                print('*')
                self.cur.execute("""INSERT INTO childrens(familia, name, count) VALUES (?, ?, 1)""",
                                 (self.fam, self.name))

            # внесение изменений в БД по ученику после работы
            id_im = self.cur.execute("""SELECT ID FROM files WHERE image = ?""",
                                     (self.comboBox.currentText(),)).fetchone()
            print(id_im)
            n = self.cur.execute("""SELECT count, average_mark FROM childrens WHERE familia = ? and name = ?""",
                                 (self.fam, self.name)).fetchone()
            n = list(n)
            print(n)
            if str(n[1]).isalpha():
                n[1] = '0'
            elif not n[1]:
                n[1] = self.o
            print(n)
            self.cur.execute(
                """UPDATE childrens SET count = ?, images = ?, average_mark = ? WHERE familia = ? and name = ?""",
                (n[0] + 1, id_im[0], str((float(n[1]) + float(self.o)) / 2), self.fam, self.name))
            print(*res)
            self.con.commit()
            sys.exit(app.exec_())

    def select_task(self, text):
        # работа с базой рисунков - определение пути к файлу из БД
        # Подключение к БД
        # запрос на путь к файлу с рисунком
        result = self.cur.execute("""SELECT name_file FROM files
                            WHERE image = ?""", (self.comboBox.currentText(),)).fetchone()[0]
        print(result)
        # запрос на путь к файлу с координатами
        result_1 = self.cur.execute("""SELECT koord_file FROM files
                            WHERE image = ?""", (self.comboBox.currentText(),)).fetchone()[0]
        print(result_1)
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
        print(self.coord)
        self.ans = ''

    def ok(self):
        # ввод фамилии ребенка
        self.fam = self.lineEdit_3.text()
        print(self.fam)
        # ввод имени ребенка
        self.name = self.lineEdit_4.text()
        print(self.name)
        # проверка корректности ввода фамилии и имени
        try:
            if not self.fam.isalpha() and not self.name.isalpha():
                mess = 'Ошибка при вводе имени и фамилии: присутствуют посторонние символы!'
                raise ValueError(mess)
            elif self.fam.isalpha() and not self.name.isalpha():
                mess = 'Ошибка при вводе имени: присутствуют посторонние символы!'
                raise ValueError(mess)
            elif self.name.isalpha() and not self.fam.isalpha():
                mess = 'Ошибка при вводе фамилии: присутствуют посторонние символы!'
                raise ValueError(mess)
            else:
                # поиск ребенка по базе - если есть, то фиксируем ID, если нет, то добавляем в базу новый ID и данные
                # Выполнение запроса и получение всех результатов
                res = self.cur.execute("""SELECT ID FROM childrens WHERE familia = ? and name = ?""",
                                       (self.fam, self.name)).fetchall()
                print(res)
                if not res:
                    print('*')
                    self.con.execute(
                        """INSERT INTO childrens(familia, name) VALUES (?, ?)""",
                        (self.fam, self.name))

                self.con.commit()
        except ValueError:
            self.label_8.setText(f"Ошибка! {mess}")


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.excepthook = except_hook
sys.exit(app.exec_())
