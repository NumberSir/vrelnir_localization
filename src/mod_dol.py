# from typing import Any



# mod_dol_default = {
#         "name": "",
#         "zh_name": "",
#         "type": "",
#         "project_id": -1,
#         "author": "",
#         "url": "",
#         "main_branches": "",
#         "dev_branches": "",
#         "path": ""
# }
# class ModDol(object):
#     def __init___(self):
#         self._data:dict[str,Any] = {"name": "","zh_name": "","type": "","project_id": -1,"author": "","url": "","main_branches": "","dev_branches": "","path": ""}
#     @property
#     def data(self):
#         return self._data
#     @property
#     def name(self):
#         print(self.data)
#         return self.getter_key("name")
#     @name.setter
#     def name(self,value):
#         self.setter_key("name",value)
#     @property
#     def zh_name(self):
#         return self.getter_key("zh_name")
#     @zh_name.setter
#     def zh_name(self,value):
#         self.setter_key("zh_name",value)
#     @property
#     def type(self):
#         return self.getter_key("type")
#     @type.setter
#     def type(self,value):
#         self.setter_key("type",value)
#     @property
#     def project_id(self):
#         return self.getter_key("project_id")
#     @project_id.setter
#     def project_id(self,value):
#         self.setter_key("project_id",value)
    
    
    
#     def getter_key(self,key:str):
#         if not key:
#             return None
#         value = self.data[key]
#         if value:
#             return value
#         default_value =mod_dol_default[key]
#         self.data[key] = default_value
#         return default_value
        
#     def setter_key(self,key:str,value:Any):
#         self.data[key] = value
   
        



 

# mod_dol = ModDol()
# print(mod_dol.name)