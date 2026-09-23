class CipherMaster:
    # Не изменяйте и не перемещайте эту переменную
    alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'

    def cipher(self, original_text, shift):
        # Метод должен возвращать зашифрованный текст
        # с учетом переданного смещения shift.
        result = []
        for letter in original_text:
            letter = letter.lower()
            if letter not in self.alphabet:
                result.append(letter)  
                return ''.join(result)                     # не-буква → как есть
            else:
                position = self.alphabet.index(letter)     # номер буквы
                new_position = (position + shift) % 33     # сдвиг с зацикливанием
                result.append(self.alphabet[new_position]) # буква по новому номеру
                return ''.join(result) 
    #def decipher(self, cipher_text, shift):
        # Метод должен возвращать исходный текст
        # с учётом переданного смещения shift.
        #result = []
        


cipher_master = CipherMaster()
print(cipher_master.cipher('мама мыла раму', 2))   # овов оэнв твох
print(cipher_master.cipher('МаМа', 2))              # всё маленькими
print(cipher_master.cipher('я', 2))                 # б (зацикливание)