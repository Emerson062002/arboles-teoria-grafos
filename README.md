# Árboles en teoría de grafos: algoritmo de Kruskal

Este proyecto calcula árboles generadores mínimos de grafos ponderados con Kruskal y Prim. La consola muestra las decisiones de Kruskal y compara ambos resultados; la página web visualiza las aristas, explica cada paso y permite ingresar grafos propios.

El núcleo de dominio Python es compartido por la consola y la página web mediante un servidor local. No se requieren paquetes externos ni conexión a internet.

La fuente de verdad de ambos algoritmos está en Python. El JavaScript solo solicita análisis al servidor y actualiza la visualización y los controles.

## ¿Qué problema resuelve?

Una empresa quiere conectar cinco oficinas con la menor cantidad de cable posible. No necesita un cable entre cada par: basta con que haya un camino entre todas, y un cable de sobra solo cerraría un ciclo. Esa red es un **árbol generador mínimo**: conecta todos los puntos, no tiene ciclos y suma el menor peso posible. Este proyecto la calcula con Kruskal y Prim, muestra las decisiones de Kruskal y comprueba que ambos algoritmos obtengan el mismo peso mínimo.

## Cómo funciona y por qué funciona

1. Se ordenan las aristas de menor a mayor peso.
2. Se recorren en ese orden. Si los extremos de una arista están en componentes distintas, se agrega. Si ya estaban conectados, se descarta porque cerraría un ciclo.
3. Se termina al tener `n - 1` aristas, que es lo que tiene un árbol de `n` vértices.

La elección es segura porque, entre dos componentes que todavía están separadas, la arista más liviana que las conecta puede formar parte de un árbol mínimo: reemplazar por ella una conexión más pesada no aumenta el costo y mantiene la conexión. Al repetir esta elección sin crear ciclos, Kruskal obtiene un árbol generador mínimo si el grafo es conexo.

Si `V` es el número de vértices y `E` el de aristas, ordenar las aristas toma `O(E log E)`. Las operaciones de unión y búsqueda de componentes son casi constantes en la práctica, así que ordenar domina el tiempo total.

## Ejemplo resuelto

El grafo de ejemplo tiene cinco vértices (A, B, C, D, E) y estas aristas: AB = 4, AC = 2, BC = 1, BD = 5, CD = 8, CE = 10 y DE = 2. El algoritmo decide así:

| Arista | Peso | Decisión |
| --- | --- | --- |
| BC | 1 | Se agrega |
| AC | 2 | Se agrega |
| DE | 2 | Se agrega |
| AB | 4 | Se descarta: cerraría el ciclo A-B-C |
| BD | 5 | Se agrega; al tener cuatro aristas, termina |

Árbol generador mínimo: `BC`, `AC`, `DE` y `BD`, con peso total `1 + 2 + 2 + 5 = 10`. Las aristas CD (8) y CE (10) no se examinan porque el árbol ya tiene `n - 1` aristas.

## Casos que conviene conocer

- **Grafo no conexo:** no existe árbol generador. Python informa que no es conexo y muestra el bosque mínimo de sus componentes; la página también indica que no se pudieron conectar todos los vértices.
- **Vértices aislados:** la página permite ingresar un grafo sin aristas; si solo se ingresa un vértice, se reconoce como el árbol trivial.
- **Empates de peso:** el árbol mínimo puede no ser único, pero su peso total siempre es el mismo. En el ejemplo, AC y DE pesan 2 y ambas se agregan.
- **Decimales y pesos negativos:** se admiten pesos numéricos finitos, como `2.5` o `-1`.
- **Vértices aislados:** Python permite indicarlos al llamar `kruskal(aristas, vertices)`, aunque no aparezcan en ninguna arista.
- **Entradas inválidas:** la función rechaza vértices repetidos, extremos no declarados, lazos, aristas duplicadas y pesos no finitos.

## Conexión con la teoría

| Concepto de la materia | Dónde aparece en el proyecto |
| --- | --- |
| Árbol: grafo conexo y sin ciclos | La comprobación final del resultado |
| Un árbol de `n` vértices tiene `n - 1` aristas | El criterio para detener el algoritmo |
| Árbol generador mínimo | Lo que calcula Kruskal |
| Ciclo | La razón por la que se descarta una arista |

## Abrir la página visual

Inicia el servidor local con Python desde la carpeta del proyecto y abre la dirección indicada en el navegador. La página ya no se abre directamente como archivo: solicita los cálculos al núcleo Python para que la consola y la web usen la misma lógica. No necesitas instalar paquetes ni tener conexión a internet. El grafo se muestra en un lienzo 3D con perspectiva y profundidad: gira suavemente, se puede rotar arrastrando con el mouse o el dedo, y el botón **Pausar giro** permite detener el movimiento. La preferencia del navegador para reducir movimiento se respeta. Selecciona un vértice haciendo clic en el punto o en su nombre: el panel explica cuántas conexiones tiene, sus vecinos y pesos, y si cada arista está pendiente, incluida en el árbol, descartada por cerrar un ciclo o no fue necesaria para terminar Kruskal. También puedes enfocar el lienzo y usar las flechas del teclado para recorrer los vértices.

Pulsa **Ver primer paso** y luego **Ver siguiente paso** para observar cómo se construye el árbol; usa **Anterior** para regresar una decisión o **Ver todo** para completar el recorrido. **Reiniciar** vuelve al inicio del grafo actual y **Cargar ejemplo original** restaura el ejemplo de cinco vértices. La página muestra explicaciones, estadísticas de Kruskal y una comparación de peso y aristas con Prim. Si el grafo es desconectado, ambos algoritmos calculan un bosque mínimo.

### Ingresar otro grafo

En la sección **Ingresa tu propio grafo**, reemplaza los vértices separados por comas y escribe cada arista en una línea con este formato:

```text
origen, destino, peso
```

Por ejemplo:

```text
Ana, Luis, 3
Luis, Marta, 7
Ana, Marta, 5
```

Los nombres de los extremos deben estar incluidos en la lista de vértices. Pulsa **Calcular este grafo** para actualizar el dibujo y recorrer el algoritmo. Los pesos pueden ser números enteros o decimales. Si el grafo no es conexo, la página lo indicará. El servidor valida y calcula el grafo sin modificar archivos del proyecto.

## Requisitos

- Python 3.8 o superior
- No se requieren paquetes externos.

## Ejecutar en Windows

Abre PowerShell y ejecuta:

```powershell
cd "C:\Users\EMERSON\OneDrive\Escritorio\matematicas discretas"
py .\index.py
```

Para usar la interfaz web, ejecuta en PowerShell:

```powershell
py -m kruskal_app.adapters.web
```

Luego abre en el navegador la dirección que aparece (por defecto `http://127.0.0.1:8000`). Detén el servidor con `Ctrl+C`. Si el comando `py` no está disponible, reemplázalo por `python`.

### Permitir acceso desde otra computadora de la misma red

De forma predeterminada, el servidor solo acepta conexiones desde esta PC. Para que otros equipos conectados a la misma red local puedan abrirlo, inicia el servidor escuchando en todas las interfaces:

```powershell
py -m kruskal_app.adapters.web --host 0.0.0.0 --port 8000
```

En la PC que ejecuta el servidor, consulta su dirección IPv4 con `ipconfig` y busca el adaptador de red que comparte con la otra computadora. Desde el otro equipo, abre `http://DIRECCION-IP:8000`, reemplazando `DIRECCION-IP` por esa dirección (por ejemplo, `http://192.168.1.25:8000`). Ambos equipos deben estar en la misma red y, si Windows muestra un aviso del firewall, permite Python solo en redes privadas. Si el puerto 8000 ya está ocupado, elige otro, como `8003`, tanto al iniciar como al abrir la dirección.

Esta modalidad es para una red local confiable; no configures el router para publicar el puerto en internet. Para compartir la web fuera de tu red se necesita desplegarla en un servidor con medidas de seguridad adecuadas.

### Publicar en internet con Render

El archivo `render.yaml` configura el servicio web para Render. Sube el código a un repositorio de GitHub y, en Render, crea un **Blueprint** desde ese repositorio. Render detectará la configuración y asignará una URL pública estable; no tendrás que compartir la IP de tu computadora ni mantenerla encendida. El plan gratuito puede suspender el servicio cuando está inactivo, por lo que la primera visita después de una pausa puede tardar.

## Ejecutar en macOS o Linux

Desde la carpeta del proyecto, ejecuta:

```bash
python3 index.py
```

Para iniciar la interfaz web:

```bash
python3 -m kruskal_app.adapters.web
```

Abre `http://127.0.0.1:8000` en el navegador y detén el servidor con `Ctrl+C`.

Para permitir acceso desde otros equipos de la red, inicia con `--host 0.0.0.0` y comparte la dirección IPv4 de esta computadora, por ejemplo `http://192.168.1.25:8000`. Los equipos deben compartir una red local confiable.

## Usar un archivo de grafo en la consola

Se puede pasar un archivo UTF-8 con una arista por línea:

```text
A, B, 4
A, C, 2
B, C, 1
```

Las líneas vacías y las que empiezan con `#` se ignoran. Para ejecutarlo:

```powershell
py .\index.py .\grafo.txt
```

La consola presenta las decisiones de Kruskal y compara el bosque mínimo de Prim.

## Pruebas automáticas

Ejecuta las pruebas desde la carpeta del proyecto:

```powershell
py -m unittest
```

También puedes usar `python -m unittest` si no tienes disponible el comando `py`. Se prueban el ejemplo, empates, decimales, pesos negativos, grafos desconectados, vértices aislados, entradas inválidas, la comparación de algoritmos y el adaptador HTTP.

## Resultado esperado

Para el grafo de ejemplo, Kruskal y Prim encuentran un árbol de peso total `10` con cuatro aristas. La consola imprime las decisiones de Kruskal, las estadísticas y el resultado de Prim.

## Cambiar el grafo

Las aristas y sus pesos del ejemplo están definidas en `kruskal_app/adapters/console.py`. Cada elemento tiene el formato:

```python
("origen", "destino", peso)
```

Cambia esa lista para probar otro grafo en la consola. En la web puedes ingresar un grafo nuevo sin editar el código.

## Arquitectura hexagonal

```text
kruskal_app/
├── domain/
│   ├── grafo.py       # Modelo y validación del grafo
│   ├── union_find.py  # Componentes disjuntos
│   ├── kruskal.py     # Kruskal y pasos
│   ├── prim.py        # Prim y bosque mínimo
│   └── resultado.py   # Modelos de pasos, resultados y comparación
├── application/
│   ├── ports.py       # Puerto de entrada
│   └── use_cases.py   # Caso de uso AnalyzeGraph
├── adapters/
│   ├── console.py     # Adaptador de consola
│   └── web.py         # Servidor HTTP local
├── tests/             # Pruebas del dominio y adaptador HTTP
└── web/
    ├── index.html     # Estructura de la interfaz
    ├── style.css      # Presentación
    └── app.js         # Peticiones HTTP y controles visuales
index.py               # Punto de entrada de consola
```

El dominio solo importa módulos del propio dominio o de la biblioteca estándar; no depende de `application` ni de los adaptadores. La consola y el servidor llaman al caso de uso `AnalyzeGraph`. La página web envía los datos mediante `POST /api/analyze`; el servidor valida el JSON y devuelve los pasos, los resultados y las estadísticas serializados. Los archivos estáticos se sirven desde el propio servidor local.

## Conclusión

El ejemplo muestra que no es necesario conectar cada par de vértices: al tomar primero las conexiones más livianas sin cerrar ciclos, Kruskal construye una red de costo mínimo. La verificación de conectividad y del número de aristas permite confirmar que la solución obtenida sí es un árbol.

## Autor

[Tu nombre] · Matemáticas Discretas · [Universidad] · 2026
