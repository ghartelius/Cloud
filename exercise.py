class Dog:
    def __init__(self,sound):
        self.sound = sound 
        #laver en tom liste til de tricks som hunden skal kunne
        self.list_of_tricks =[]
    
    def make_sound(self):
        return self.sound
    
    def add_trick(self,trick):
        return self.list_of_tricks.append(trick)
    
    
if __name__ == '__main__':
    d1 = Dog("vov")
    d2 = Dog("vuf (på svensk)")
   
    #tilføjer tricks til hundens trick-register
    d1.add_trick("jump")
    d1.add_trick("roll")

    print(d1.make_sound())
    print(d1.list_of_tricks)
    print("Balto siger "+ d1.make_sound())
    print("Duro siger "+ d2.make_sound())


