# -*- coding: utf-8 -*-
"""
File for all functions
"""
from qgis.core import QgsProject, QgsGeometry, QgsPoint

# --- Attibute filters --------------------------------------------------------
FILTERS = ['equals', 'bigger_than', 'bigger_or_equal', 'smaller_than', 'smaller_or_equal', 'contains']

def no_filter(layer_name, no, noo, nooo):
    features = []
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    for feat in layer.getFeatures():
        features.append(feat)
    return features

def equals(layer_name, field, value, is_numeric):
    filtered = []
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    idx = layer.fields().lookupField(field)
    for feat in layer.getFeatures():
        if str(feat.attributes()[idx]) == value:
            filtered.append(feat)
    return filtered

def bigger_than(layer_name, field, value, is_numeric):
    filtered = []
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    idx = layer.fields().lookupField(field)
    for feat in layer.getFeatures():
        if is_numeric:
            value = float(value)
        if feat.attributes()[idx] > value:
            filtered.append(feat)
    return filtered

def bigger_or_equal(layer_name, field, value, is_numeric):
    filtered = []
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    idx = layer.fields().lookupField(field)
    for feat in layer.getFeatures():
        if is_numeric:
            value = float(value)
        if feat.attributes()[idx] >= value:
            filtered.append(feat)
    return filtered

def smaller_than(layer_name, field, value, is_numeric):
    filtered = []
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    idx = layer.fields().lookupField(field)
    for feat in layer.getFeatures():
        if is_numeric:
            value = float(value)
        if feat.attributes()[idx] < value:
            filtered.append(feat)
    return filtered

def smaller_or_equal(layer_name, field, value, is_numeric):
    filtered = []
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    idx = layer.fields().lookupField(field)
    for feat in layer.getFeatures():
        if is_numeric:
            value = float(value)
        if feat.attributes()[idx] <= value:
            filtered.append(feat)
    return filtered

def contains(layer_name, field, value, is_numeric):
    filtered = []
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    idx = layer.fields().lookupField(field)
    for feat in layer.getFeatures():
        if value in str(feat.attributes()[idx]):
            filtered.append(feat)
    return filtered

# --- layer.geometryType() ----------------------------------------------------

FUNCTIONS = {
# 0 - point, 1 - line, 2 - polygon
# function_name: {
#     'geom1_type': geometry type of first layer
#     'geom2_type': geometry type of second layer
# }

    'must_not_have_duplicates': {
        'geom1_type': [0,1,2],
        'geom2_type': '',
    },
    'must_not_intersect': { #intersection
        'geom1_type': [2],
        'geom2_type': '',
    },
    'must_not_intersect_with': {
        'geom1_type': [2],
        'geom2_type': [2],
    },
    'must_be_inside': {
        'geom1_type': [0,1,2],
        'geom2_type': [2],
    },
    'must_contain': {
        'geom1_type': [2],
        'geom2_type': [0,1,2],
    },
    'must_not_contain': {
        'geom1_type': [2],
        'geom2_type': [0,1,2],
    },
    'must_not_cross': {
        'geom1_type': [1],
        'geom2_type': '',
    },
    'must_not_cross_with': {
        'geom1_type': [1],
        'geom2_type': [1],
    },
    'ends_must_be_covered': {
        'geom1_type': [1],
        'geom2_type': [0],
    },
    'must_be_endpoint': {
        'geom1_type': [0],
        'geom2_type': [1],
    },

}


def must_not_intersect(features):
    result = []
    for i in range(len(features)):
        for j in range(i+1, len(features)):
            if features[i].geometry().intersects(features[j].geometry()):
                result.append([features[i].id(), 'intersects_with', features[j].id()])
    return result

def must_not_intersect_with(features, features2):
    result = []
    for i in range(len(features)):
        for j in range(len(features2)):
            if features[i].geometry().intersects(features2[j].geometry()):
                result.append([features[i].id(), 'intersects_with', features2[j].id()])
    return result

def must_contain(features, features2):
    contains = []
    result = []
    for i in range(len(features)):
        for j in range(len(features2)):
            if features[i].geometry().contains(features2[j].geometry()):
                contains.append(i)
    for i in range(len(features)):
        if i not in contains:
            result.append([features[i].id(), 'does_not_contain', None])
    return result

def must_not_contain(features, features2):
    contains = []
    result = []
    for i in range(len(features)):
        for j in range(len(features2)):
            if features[i].geometry().contains(features2[j].geometry()):
                contains.append(i)
    for i in range(len(features)):
        if i in contains:
            result.append([features[i].id(), 'contains', None])
    return result

def must_be_inside(features, features2):
    within = []
    result = []
    for i in range(len(features)):
        for j in range(len(features2)):
            if features[i].geometry().within(features2[j].geometry()):
                within.append(i)
    for i in range(len(features)):
        if i not in within:
            result.append([features[i].id(), 'is_not_in', None])
    return result

def must_be_on(points, lines):
    within = []
    result = []
    for i in range(len(points)):
        for j in range(len(lines)):
            if points[i].geometry().intersects(lines[j].geometry()):
                within.append(i)
    for i in range(len(points)):
        if i not in within:
            result.append([points[i].id(), 'is_not_on', None])
    return result

def must_not_have_duplicates(features):
    result = []
    for i in range(len(features)):
        for j in range(i+1, len(features)):
            if features[i].geometry().equals(features[j].geometry()):
                result.append([features[i].id(), 'duplicates_with', features[j].id()])
    return result

def must_not_cross(features):
    result = []
    for i in range(len(features)):
        for j in range(i+1, len(features)):
            if features[i].geometry().intersects(features[j].geometry()):
                result.append([features[i].id(), 'crosses_with', features[j].id()])
    return result

def must_not_intersect_with(features, features2):
    result = []
    for i in range(len(features)):
        for j in range(len(features2)):
            if features[i].geometry().intersects(features2[j].geometry()):
                result.append([features[i].id(), 'crosses_with', features2[j].id()])
    return result

def ends_must_be_covered(lines, points):
    good = []
    result = []
    for i in range(len(lines)):
        not_covered = ['start_point', 'end_point']
        line = lines[i].geometry().asPolyline()
        start_point = QgsPoint(line[0])
        end_point = QgsPoint(line[-1])
        for j in range(len(points)):
            point = QgsPoint(points[j].geometry().asPoint())
            if 'start_point' in not_covered:
                if start_point == point:
                    not_covered.remove('start_point')
            if 'end_point' in not_covered:
                if end_point == point:
                    not_covered.remove('end_point')
            if not not_covered:
                good.append(i)
                break
    for i in range(len(lines)):
        if i not in good:
            result.append([lines[i].id(), 'ends_not_covered', None])
    return result

def must_be_endpoint(points, lines):
    good = []
    result = []
    for i in range(len(points)):
        for j in range(len(lines)):
            line = lines[j].geometry().asPolyline()
            start_point = QgsPoint(line[0])
            end_point = QgsPoint(line[-1])
            point = QgsPoint(points[i].geometry().asPoint())
            if (point == start_point or point == end_point):
                good.append(i)
    for i in range(len(points)):
        if i not in good:
            result.append([points[i].id(), 'is_not_at_end', None])
    return result
