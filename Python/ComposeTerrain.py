import os

import numpy as np
import PIL
from PIL import Image

terrainPath = "C:/Users/<path to an extracted map folder>"

def composeHeightmap(terrainPath, mapSizeX, mapSizeY, outputPath = "Output"):
    heightmapTileWidth = 131
    heightmapTileHeight = 131
    compositeTileWidth = 128
    compositeTileHeight = 128
    compositeWidth = compositeTileWidth * int(mapSizeX)
    compositeHeight = compositeTileHeight * int(mapSizeY)
    composite = PIL.Image.new("I;16", (compositeWidth, compositeHeight))

    for y in range(0, 5):
        for x in range(0, 4):
            tileFile = open(terrainPath + "/" + "00" + str(x) + "00" + str(y) + "/height.raw", "rb")
            tileRaw = tileFile.read()
            tileFile.close()
            tileImage = PIL.Image.frombuffer("I;16", (heightmapTileWidth, heightmapTileHeight), tileRaw)
            compositePasteX = x * compositeTileWidth
            compositePasteY = y * compositeTileHeight
            composite.paste(tileImage, (compositePasteX, compositePasteY))

    # Save composite heightmap as raw.
    compositeFile = open(outputPath + "/heightmap.r16", "wb")
    compositeFile.write(composite.tobytes())
    compositeFile.close()

    # Save composite heightmap as image.
    composite.save(outputPath + "/heightmap.png")

def composePaintLayers(terrainPath, mapSizeX, mapSizeY, outputPath = "Output"):
    terrainTileWidth = 128
    terrainTileHeight = 128
    splatmapTileWidth = 258
    splatmapTileHeight = 258
    compositeTileWidth = 258
    compositeTileHeight = 258
    compositeWidth = compositeTileWidth * int(mapSizeX)
    compositeHeight = compositeTileHeight * int(mapSizeY)
    composite = PIL.Image.new("L", (compositeWidth, compositeHeight))

    for y in range(0, int(mapSizeY)):
        for x in range(0, int(mapSizeX)):
            tileFile = open(terrainPath + "/" + "00" + str(x) + "00" + str(y) + "/tile.raw", "rb")
            tileRaw = tileFile.read()
            tileFile.close()
            tileImage = PIL.Image.frombuffer("L", (splatmapTileWidth, splatmapTileHeight), tileRaw)
            compositePasteX = x * compositeTileWidth
            compositePasteY = y * compositeTileHeight
            composite.paste(tileImage, (compositePasteX, compositePasteY))

    # Split colors of composite splat map as layers.
    layers = dict()

    for color in composite.getcolors():
        layers[color[1]] = PIL.Image.new("L", (compositeWidth, compositeHeight))

    for y in range(0, compositeHeight):
        for x in range(0, compositeWidth):
            color = composite.getpixel((x, y))
            layers[color].putpixel((x, y), 255)

    terrainDimensions = (
        (terrainTileWidth - 0) * mapSizeX + 0,
        (terrainTileHeight - 0) * mapSizeY + 0,
    )

    # Resize composite to match terrain dimensions.
    composite = composite.resize(terrainDimensions, PIL.Image.LANCZOS)

    # Save composite splat map as raw.
    compositeFile = open(outputPath + "/splatmap.r16", "wb")
    compositeFile.write(composite.tobytes())
    compositeFile.close()

    # Save composite splat map as image.
    composite.save(outputPath + "/splatmap.png")

    # Save layers as paint layers.
    for (index, layer) in layers.items():
        # Resize layer to match terrain dimensions.
        layer = layer.resize(terrainDimensions, PIL.Image.LANCZOS)

        # Save as raw.
        paintLayerFile = open(outputPath + "/paintlayer_%s.r16" % index, "wb")
        paintLayerFile.write(layer.tobytes())
        paintLayerFile.close()

        # Save as image.
        layer.save(outputPath + "/paintlayer_%s.png" % index)

def composeTerrain(terrainPath, outputPath = "Output"):
    mapSettingsPath = terrainPath + "/setting.txt"
    mapSettingsLines = open(mapSettingsPath, "r", encoding="utf8", errors='ignore').readlines()
    mapSizeX = 0
    mapSizeY = 0

    for line in mapSettingsLines:
        parts = line.split()
        if len(parts) == 0:
            continue
        name = parts[0]
        if (name == "MapSize"):
            mapSizeX = int(parts[1])
            mapSizeY = int(parts[2])

    os.makedirs(outputPath, exist_ok=True)

    composeHeightmap(terrainPath, mapSizeX, mapSizeY, outputPath)
    composePaintLayers(terrainPath, mapSizeX, mapSizeY, outputPath)

composeTerrain(terrainPath)
