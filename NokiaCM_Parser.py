import xml.etree.ElementTree as et
import pandas as pd
import os
import time as dt
from tqdm import tqdm


start = dt.time()

'''Define directory and file name for parsing'''
file_directory = r'\path\to\folder'
file_name = r'file_name.xml'

path_to_file = os.path.join(file_directory, file_name) 
path_for_parsing_results = path_to_file.replace('.xml', '_prasing_results') # folder for results
if not os.path.exists(path_for_parsing_results): #create folder if needed
     os.mkdir(path_for_parsing_results)

tree = et.parse(path_to_file)
root = tree.getroot()  

'''Define raml version depending on eNB SW version'''

raml='{raml21.xsd}managedObject' 
# raml='{raml20.xsd}managedObject'

'''Collest all manage objects from the file'''
objs = []
for MO in root.iter(raml):   # iter through tag managedObject 
    objname = MO.get('class')
    if objname not in objs:                      # содержание атрибута class = имя_объекта
        objs.append(objname)                     # пишем имена объектов в лист

objs = list(set(objs))                           # удаляем дубликаты с
print(f'Objects are collected')

### Надо пробегать по каждому managedObject, внутри него пройтись по каждому параметру, 
### собирать все имена и все значения в строку для каждого DN, сделать словарь, сделать список со словарями, из списка словарей сделать DataFrame, записать DF в .csv

for mo_class_name in  tqdm(objs, desc='Managed objects parsing status'):                         ### так как мы ранее собрали полный список объектов во всем файле, то будем пробегаться по каждому из этого списка
        all_names_and_values = []                           ### это основный список, сюда складываем словари по объектам
        for o in root.iter(raml):    ### заводим итератор по тэгу managedObject
            if o.attrib['class'] == mo_class_name:          ### заходим в managedObject с нужным именем класса
                mo_para_name = o.keys()                     ### имена идентификаторов объекта. тут словарь, берем только ключи, они будут в формате листа
                mo_para_value =  list(o.attrib.values())    ### значения идентификатора объекта. тут словарь, берем значения и кидаем в лист
                para_names, para_values, all_val, all_names = [], [], [], []
                for i in o.iter('{raml21.xsd}p'):        ### опускаемся внутрь managedObject до тэга p (то есть параметров) и  там запускаем итератор, чтобы забрать имена и значения параметров
                    child_para_name =  list(i.attrib.values())       ### забираем имя параметра и кидаем в лист
                    temp_para_value =  i.text                        ### забираем значение параметра, тут тип данных str, нам нужен лист чтобы слепить с mo_para_value
                    child_para_value = []                            ### создаем пустой лист
                    child_para_value.append(temp_para_value)         ### и в него будем каждый раз записывать temp_para_value. на выходе будет лист
                    if len(child_para_name) > 0:                     ### исключаем пустые объекты
                        para_names.append(child_para_name[0])        ### формируем лист именами параметров
                        para_values.append(child_para_value[0])      ### формируем лист с значениями параметров
                para_values_for_all_DN = mo_para_value + para_values ### добавляем к значениям параметров значения идентификаторов: ['class', 'version', 'distName', 'id']
                all_val.append(para_values_for_all_DN)               ### тут объединяем значеня параметров по всем объектам одного класса, которые собрались в цикле выше
                para_names_for_all_DN = mo_para_name + para_names    ### добавляем к именам параметров имена идентификаторов: ['class', 'version', 'distName', 'id']
                all_names.append(para_names_for_all_DN)              ### тут объединяем имена параметров по всем объектам одного класса, которые собрались в цикле выше
                dict_names_and_values = dict(zip(all_names[0], all_val[0]))     ### делаем словарь для каждого объекта одного класcа {para1: para_value1; para2: para_value2 }
                all_names_and_values.append(dict_names_and_values)              ### каждый такой словарь добавляем в list. получится список с набором словарей для каждого объекта
        df_mo = pd.DataFrame(all_names_and_values)      ### когда цикл по всем объектам одного класса закончится и лист наполнится словарями, то его можно будет писать в DataFrame
                                                        ### это фича по умолчанию работает как надо: если список параметров в разных объектах будет разный - это фича автоматом добавит столбец.
                                                        ### в тех объектах где такого столбца нет проставит NaN.
        '''For some versions, especially SRAN, mo class contains dots and : , it leads to unsupported file name'''
        clear_mo_class_name = mo_class_name[mo_class_name.find(':')+1:]
        '''to csv'''                                                
        # df_mo.to_csv(os.path.join(path_for_parsing_results, f'{clear_mo_class_name}.csv'), index = False)
        '''or to xlsx with transponse'''
        df_mo.set_index(df_mo.columns[0]).transpose().to_excel(os.path.join(path_for_parsing_results, f'{clear_mo_class_name}.xlsx'))
stop = dt.time()
print(f'Processing finished. Elapsed time = {round(stop - start,2)}')
