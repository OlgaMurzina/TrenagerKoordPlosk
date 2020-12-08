import sqlite3
import sys

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow

from design_form import Ui_MainWindow


class MyWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.ans = set()
        self.coord = []
        self.ans = ''  # строка координат, которые ввел пользователь
        self.count_koord = 0 # счетчик координат,которые вввел пользователь
        self.error = 0
        self.images = []
        self.count_finish = 0

        # обработка нажатия кнопки-подтверждения ввода данных ребенка
        self.pushButton_3.clicked.connect(self.ok)

        # блок выбора рисунка для задания
        # выбор рисунка по названию
        self.con2 = sqlite3.connect("SQLiteStudio\koord_pl.db")
        # Создание курсора
        self.cur2 = self.con2.cursor()
        self.images = list(map(lambda x: x[0], self.cur2.execute("""SELECT image FROM files WHERE ID > 0 """).fetchall()))
        print(self.images)
        self.comboBox.addItems(self.images)
        # вызов загрузки стартового рисунка - первого в списке комбобокса
        self.select_task(self.images[0][0])
        # вызов обработчика выбора названия рисунка в комбобоксе
        self.comboBox.activated.connect(self.select_task)

        # вызов обработчика нажатия кнопки Проверить
        self.pushButton.clicked.connect(self.run)
        # обработка нажатия ребенком кнопки Закончить
        self.pushButton_2.clicked.connect(self.finish)

    def run(self):
        # проверка наличия такого кортежа в файле рисунка и вердиткт - есть или нет
        # ввод координаты Х
        self.x = self.lineEdit_2.text()
        # ввод координаты Y
        self.y = self.lineEdit.text()
        # сравнение координат с координатами из файла к выбранному рисунку
        koord = str(self.x) +';' + str(self.y)
        print(koord, self.coord)
        # выставление оценки, если все координаты введены или сообщение о коорректоности ответа
        if not(self.coord):
            if (self.count_koord - self.error) / self.count_koord > 0.85:
                o = '5'
            elif 0.68 <= (self.count_koord - self.error) / self.kount_coord <= 0.85:
                o = '4'
            elif 0.5 <= (self.count_koord - self.error) / self.kount_coord <= 0.67:
                o = '3'
            else:
                o = 'Нужно еще поработать с теорией'
            self.label_8.setText(f"Работа завершена успешно!\nОшибок - {self.error}\nОценка - {o}")
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
            self.label_8.setText("Неверно.\nПопробуйте еще раз.")
            self.error += 1
        self.lineEdit_2.setText('')
        self.lineEdit.setText('')



    def finish(self):
        # нажатие кнопки Закончить работу с учетом повторного нажатия
        # в идеале - диалоговое окно про все равно закончить
        self.count_finish += 1
        if self.coord and self.count_finish == 1:
            self.label_8.setText('Вы не закончили уражнение. \nВсе введенные данные \nбудут потеряны.')
        else:
            # Подключение к БД
            con1 = sqlite3.connect("SQLiteStudio\koord_pl.db")
            # Создание курсора
            cur1 = con1.cursor()
            # Выполнение запроса и получение всех результатов
            res = cur1.execute("""SELECT ID FROM childrens WHERE familia = ? and name = ?""",
                               (self.fam, self.name)).fetchall()
            print(res)
            if not res:
                print('*')
                cur1.execute("""INSERT INTO childrens(familia, name) VALUES (?, ?)""", (self.fam, self.name))
            else:
                cur1.execute("""UPDATE childrens SET count = ?, images = ? WHERE familia = ? and name = ?""",
                               (self.fam, self.name))
                print(*res)
            con1.commit()
            sys.exit(app.exec_())

    def select_task(self, text):
        # работа с базой рисунков - определение пути к файлу из БД
        # Подключение к БД
        # выполнение запроса и получение списка всех рисунков для заполнения комбобокса
        result = self.cur2.execute("""SELECT name_file FROM files
                            WHERE image = ?""", (self.comboBox.currentText(),)).fetchall()[0][0]
        # запрос на путь к файлу с координатами
        result_1 = self.cur2.execute("""SELECT koord_file FROM files
                            WHERE image = ?""", (self.comboBox.currentText(),)).fetchall()[0][0]
        # открытие графического файла по выбранному рисунку
        self.pixmap = QPixmap(f'{result}')
        # доработать увеличение размера до размера экрана
        self.label_7.move(100, 100)
        size_window = self.label_7.size()
        self.label_7.setMaximumSize(size_window)
        # Отображаем содержимое QPixmap в объек)те QLabel
        self.label_7.setPixmap(self.pixmap)

        # связь рисунка с файлом из базы рисунков: название рисунка - ID - имя файла с координатами
        self.f = open(f'{result_1}', 'r')
        self.coord = self.f.read().split('\n')
        self.coord = set([a.strip('#') for a in self.coord])
        self.coord.remove('')
        print(self.coord)
        self.f.close()

    def app_image(self):
        # блок для учителя - добавления нового/удаления старого рисунка в БД из программы - меню файл - добавить новый рисунок/удалить старый
        pass

    def ok(self):
        # ввод фамилии ребенка
        self.fam = self.lineEdit_3.text()
        print(self.fam)
        # ввод имени ребенка
        self.name = self.lineEdit_4.text()
        print(self.name)
        # проверка корректности ввода фамилии и имени
        try:
            if self.fam.isalpha() and self.name.isalpha():
                pass
            elif self.fam.isalpha() and not self.name.isalpha():
                pass
            elif self.name.isalpha() and not self.fam.isalpha():
                pass
            else:
                pass
        except:
            pass

        # поиск ребенка по базе - если есть, то фиксируем ID, если нет, то добавляем в базу новый ID и данные
        # Подключение к БД
        con1 = sqlite3.connect("SQLiteStudio\koord_pl.db")
        # Создание курсора
        cur1 = con1.cursor()
        # Выполнение запроса и получение всех результатов
        res = cur1.execute("""SELECT ID FROM childrens WHERE familia = ? and name = ?""",
                           (self.fam, self.name)).fetchall()
        print(res)
        if not res:
            print('*')
            cur1.execute("""INSERT INTO childrens(familia, name, count, images) VALUES (?, ?, 0, 1)""", (self.fam, self.name))
        else:
            id_im = cur1.execute("""SELECT ID FROM files WHERE image = ?""", (self.comboBox.currentText(),)).fetchone()
            print(id_im)
            n = cur1.execute("""SELECT count FROM childrens WHERE familia = ? and name = ?""",
                         (self.fam, self.name)).fetchone()
            cur1.execute("""UPDATE childrens SET count = ?, images = ? WHERE familia = ? and name = ?""",
                         (n[0] + 1, id_im[0], self.fam, self.name))
            print(*res)
        con1.commit()


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.exit(app.exec_())
