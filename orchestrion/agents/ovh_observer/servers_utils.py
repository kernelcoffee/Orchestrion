KIMSUFI_FR = {
    "KS-1": "1801sk12",
    "KS-2": "1801sk13",
    "KS-3": "1801sk14",
    "KS-4": "1801sk15",
    "KS-5": "1801sk16",
    "KS-6": "1801sk17",
    "KS-7": "1801sk18",
    "KS-8": "1801sk19",
    "KS-9": "1801sk20",
    "KS-10": "1801sk21",
    "KS-11": "1801sk22",
    "KS-12": "1801sk23",
}

KIMSUFI_CA = {
    "KS-1": "1804sk12",
    "KS-4": "1804sk15",
    "KS-5": "1804sk16",
    "KS-7": "1804sk18",
    "KS-9": "1804sk20",
    "KS-10": "1804sk21",
    "KS-11": "1804sk22",
    "KS-12": "1804sk23",
}

class ServerUtils:
    def __init__(self):
        self.reference_list = (KIMSUFI_FR, KIMSUFI_CA)
        self.name_list = {}
        for refs in self.reference_list:
            inv_dict = {v: k for k, v in refs.items()}
            self.name_list = {**inv_dict, **self.name_list}

    def name_to_reference(self, name):
        result = []
        for ref_list in self.reference_list:
            if name in ref_list:
                result.append(ref_list[name])

        if not result:
            return [name]
        return result

    def reference_to_name(self, ref):
        if ref in self.name_list:
            return self.name_list[ref]
        return ref

    #  print(f"https://www.kimsufi.com/fr/order/kimsufi.xml?reference={server['hardware']}")
