import os
import shutil

import cv2
import numpy as np
import PIL
from PIL import Image, ImageEnhance

# Settings

# Set path of the map with setting.txt and tile folders 00x00y.
mapPath = 'C:/Users/<path to an extracted map folder>'

# Set texture sets path to enable extraction of textures for the map.
textureSetsPath = 'C:/Users/<path to an extracted texture sets folder>'

# Set texture maps path to enable extraction of textures for the map.
textureMapsPath = 'C:/Users/<path to an extracted texture maps folder>'

# Helpers

def underscoreToCamelCase(str):
    words = str.split('_')
    return words[0].title() + ''.join(word.title() for word in words[1:])

def spaceToUnderscore(str):
    words = str.split(' ')
    return words[0].title() + '_'.join(word.title() for word in words[1:])

def fileGetRaw(path):
    with open(path, 'rb') as file:
        return file.read()

def filePutRaw(path, data):
    with open(path, 'wb') as file:
        file.write(data)

# Compose terrain

def composeHeightmap(mapPath, mapSizeX, mapSizeY, outputPath = 'Output'):
    heightmapTileWidth = 131
    heightmapTileHeight = 131
    compositeTileWidth = 128
    compositeTileHeight = 128

    # Create composite heightmap from heightmap tiles.
    compositeWidth = compositeTileWidth * mapSizeX
    compositeHeight = compositeTileHeight * mapSizeY
    composite = PIL.Image.new('I;16', (compositeWidth, compositeHeight))

    for y in range(0, mapSizeY):
        for x in range(0, mapSizeX):
            heightmapTileDimensions = (
                heightmapTileWidth,
                heightmapTileHeight,
            )
            heightmapTilePath = mapPath + '/' + '00' + str(x) + '00' + str(y) + '/height.raw'
            heightmapTileImage = PIL.Image.frombuffer('I;16', heightmapTileDimensions, fileGetRaw(heightmapTilePath))
            compositePasteCoordinate = (
                x * compositeTileWidth,
                y * compositeTileHeight,
            )
            composite.paste(heightmapTileImage, compositePasteCoordinate)

    # Save composite heightmap as raw.
    filePutRaw(outputPath + '/Heightmap.r16', composite.tobytes())

    # Save composite heightmap as image.
    composite.save(outputPath + '/Heightmap.png')

def composePaintLayers(mapPath, mapSizeX, mapSizeY, outputPath = 'Output'):
    terrainTileWidth = 128
    terrainTileHeight = 128
    splatmapTileWidth = 258
    splatmapTileHeight = 258
    compositeTileWidth = 258
    compositeTileHeight = 258

    # Create composite paintlayer from splatmap tiles.
    compositeWidth = compositeTileWidth * mapSizeX
    compositeHeight = compositeTileHeight * mapSizeY
    composite = PIL.Image.new('L', (compositeWidth, compositeHeight))

    for y in range(0, mapSizeY):
        for x in range(0, mapSizeX):
            splatmapTileDimensions = (
                splatmapTileWidth,
                splatmapTileHeight,
            )
            splatmapTilePath = mapPath + '/' + '00' + str(x) + '00' + str(y) + '/tile.raw'
            splatmapTileImage = PIL.Image.frombuffer('L', splatmapTileDimensions, fileGetRaw(splatmapTilePath))
            compositePasteCoordinate = (
                x * compositeTileWidth,
                y * compositeTileHeight,
            )
            composite.paste(splatmapTileImage, compositePasteCoordinate)

    # Save original composite splat map as image before resizing.
    composite.save(outputPath + '/SplatmapOriginal.png')

    # Split colors of composite splat map as layers.
    layers = dict()

    for color in composite.getcolors():
        layers[color[1]] = PIL.Image.new('L', (compositeWidth, compositeHeight))

    for y in range(0, compositeHeight):
        for x in range(0, compositeWidth):
            color = composite.getpixel((x, y))
            layers[color].putpixel((x, y), 255)

    terrainDimensions = (
        terrainTileWidth * mapSizeX + 2,
        terrainTileHeight * mapSizeY + 2,
    )

    # Resize composite splat map to match terrain dimensions.
    composite = composite.resize(terrainDimensions, PIL.Image.BICUBIC)
    composite = composite.crop((
        0,
        0,
        terrainTileWidth * mapSizeX,
        terrainTileHeight * mapSizeY,
    ))

    enhancer = ImageEnhance.Sharpness(composite)
    composite = enhancer.enhance(2)

    # Save composite splat map as raw.
    filePutRaw(outputPath + '/Splatmap.r8', composite.tobytes())

    # Save composite splat map as image.
    composite.save(outputPath + '/Splatmap.png')

    # Save layers as paint layers.
    for (index, layer) in layers.items():
        # Resize layer to match terrain dimensions.
        layer = layer.resize(terrainDimensions, PIL.Image.BICUBIC)
        layer = layer.crop((
            0,
            0,
            terrainTileWidth * mapSizeX,
            terrainTileHeight * mapSizeY,
        ))

        enhancer = ImageEnhance.Sharpness(layer)
        layer = enhancer.enhance(2)

        # Save as raw.
        filePutRaw(outputPath + '/PaintLayer_%s.r8' % index, layer.tobytes())

        # Save as image.
        layer.save(outputPath + '/PaintLayer_%s.png' % index)

def composeTerrain(mapPath, mapSizeX, mapSizeY, outputPath = 'Output'):
    os.makedirs(outputPath, exist_ok=True)

    composeHeightmap(mapPath, mapSizeX, mapSizeY, outputPath)
    composePaintLayers(mapPath, mapSizeX, mapSizeY, outputPath)

def extractMapTextures(textureSetRelative, outputPath = 'Output/TerrainMaps'):
    textureSetPath = textureSetsPath + '/' + textureSetRelative.lower()
    texturePathsRelative = []

    with open(textureSetPath, 'r') as reader:
        line = reader.readline()
        texturePath = ''

        while line != '':
            if line.startswith('Start'):
                texturePath = reader.readline()
                texturePathRelative = texturePath[texturePath.index('terrainmaps') + 12:-2]
                texturePathsRelative.append(texturePathRelative)
            line = reader.readline()

    for texturePathRelative in texturePathsRelative:
        # Create output dir for texture with spaces replaced by underscore and upper camel case.
        textureOutputDir = outputPath + '/' + spaceToUnderscore(os.path.dirname(texturePathRelative))
        os.makedirs(textureOutputDir, exist_ok=True)

        # Save texture an png to output dir with spaces replaced by underscore and upper camel case
        textureSourcePath = textureMapsPath + '/' + texturePathRelative
        textureTargetPath =  outputPath + '/' + spaceToUnderscore(texturePathRelative)
        textureTargetPathPng = os.path.splitext(textureTargetPath)[0] + '.png'
        textureImage = Image.open(textureSourcePath)
        textureImage.save(textureTargetPathPng)

def composeMap(mapPath, outputPath = 'Output', outputToMapSubdir=True):
    settingsPath = mapPath + '/setting.txt'
    settingsLines = open(settingsPath, 'r').readlines()
    sizeX = 0
    sizeY = 0
    textureSetRelative = ''

    for line in settingsLines:
        parts = line.split()
        if len(parts) == 0:
            continue
        name = parts[0]
        if (name == 'MapSize'):
            sizeX = int(parts[1])
            sizeY = int(parts[2])
        elif (name == 'TextureSet'):
            textureSetRelative = parts[1].lstrip('textureset')

    # Build output path and respects if map should be saved to a subdir.
    mapOutputPath = outputPath

    if outputToMapSubdir:
        # Generate map name with underscore converted to upper camel case.
        mapName = underscoreToCamelCase(os.path.basename(mapPath))
        mapOutputPath += '/' + mapName

    # Make dir for map output.
    # os.mkdir(mapOutputPath)

    composeTerrain(mapPath, sizeX, sizeY, mapOutputPath)

    if textureSetsPath != '' and textureSetRelative != '':
        extractMapTextures(textureSetRelative, outputPath + '/TerrainMaps')

composeMap(mapPath)
