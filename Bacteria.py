class BacteriaProducer:
    # Допишите инициализатор класса:
    # Задайте два атрибута экземпляра:
    # Первый хранит максимальное количество бактерий
    # Второй хранит текущее количество бактерий (по умолчанию 0)
    def __init__(self, max_bacteria):
        self.max_bacteria = max_bacteria
        self.current_bacteria_count = 0

    def create(self):
        if self.current_bacteria_count == self.max_bacteria:
                print('Нет места под новую бактерию')
        else:
            self.current_bacteria_count += 1
            print(f'Добавлена одна бактерия. Бактерий в колонии:'
                    f' {self.current_bacteria_count}')

    def delete(self):
        if self.current_bacteria_count = 0:
            print('В популяции нет бактерий, удалять нечего')
        else:
            self.current_bacteria_count -= 1
            print(f'Одна бактерия удалена. Бактерий в колонии:'
                  f)




lab = BacteriaProducer(3)
lab.create()   # Добавлена одна бактерия. Бактерий в колонии: 1
lab.create()   # Добавлена одна бактерия. Бактерий в колонии: 2
lab.create()   # Добавлена одна бактерия. Бактерий в колонии: 3
lab.create()   # Нет места под новую бактерию     