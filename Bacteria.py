class BacteriaProducer:
    # Допишите инициализатор класса:
    # Задайте два атрибута экземпляра:
    # Первый хранит максимальное количество бактерий
    # Второй хранит текущее количество бактерий (по умолчанию 0)
    def __init__(self, max_bacteria):
        self.max_bacteria = max_bacteria
        self.current_bacteria_count = 0

 def create(self):
        if self.current_bacteria_count = self.max_bacteria:
            print('Нет места под новую бактерию')
        else:
            self.current_bacteria_count += 1






lab = BacteriaProducer(3)
print(lab.max_bacteria)             # 3
print(lab.current_bacteria_count)   # 0        