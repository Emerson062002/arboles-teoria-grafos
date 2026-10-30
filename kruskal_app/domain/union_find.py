"""Estructura de conjuntos disjuntos para detectar ciclos."""


class UnionFind:
    def __init__(self, vertices):
        self.padre = {vertex: vertex for vertex in vertices}
        self.tamano = {vertex: 1 for vertex in vertices}

    def encontrar(self, vertex):
        while self.padre[vertex] != vertex:
            self.padre[vertex] = self.padre[self.padre[vertex]]
            vertex = self.padre[vertex]
        return vertex

    def unir(self, first, second):
        first_root = self.encontrar(first)
        second_root = self.encontrar(second)
        if first_root == second_root:
            return False
        if self.tamano[first_root] < self.tamano[second_root]:
            first_root, second_root = second_root, first_root
        self.padre[second_root] = first_root
        self.tamano[first_root] += self.tamano[second_root]
        return True
