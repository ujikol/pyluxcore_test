import os
import sys
PROJECT_ROOT = '/home/mick/dev/pyluxcore_test'
sys.path.append(os.path.join(PROJECT_ROOT, 'lib'))
import pyluxcore

from functools import reduce
import operator
import array
import time
import numpy as np
from scipy import stats, signal
import imageio
from time import sleep


def add_object(scene, obj_name, mesh_name, mat_name, visible=True):
  obj_props = pyluxcore.Properties()
  obj_props.Set(pyluxcore.Property("scene.objects." + obj_name + ".shape", mesh_name))
  obj_props.Set(pyluxcore.Property("scene.objects." + obj_name + ".material", mat_name))
  obj_props.Set(pyluxcore.Property("scene.objects." + obj_name + ".camerainvisible", not visible))
  scene.Parse(obj_props)

def define_mesh(scene, name, vertices, faces, transform=None, build_normals=False):
  face_normals = []
  verts = np.array(vertices, dtype=np.float)
  vert2face = [[] for v in vertices]
  for f in faces:
    a = verts[f[1]] - verts[f[0]]
    b = verts[f[2]] - verts[f[0]]
    n = np.cross(a,b)
    n /= np.linalg.norm(n)
    if build_normals:
      build_face_normal(scene, f, verts, n)
    face_normals.append(n)
    vert2face[f[0]].append(n)
    vert2face[f[1]].append(n)
    vert2face[f[2]].append(n)
  vertex_normals = np.array(list(map(lambda v2f: reduce(operator.add, v2f), vert2face)))
  vertex_normals = np.apply_along_axis(lambda x: x / np.linalg.norm(vertex_normals, axis=1), 0, vertex_normals)
  if build_normals:
    build_vertex_normals(scene, verts, vertex_normals)
  vertex_normals = list(map(lambda n: tuple(list(n)), vertex_normals))
  scene.DefineMesh(name, vertices, faces, vertex_normals, None, None, None, None)

def build_face_normal(scene, face, verts, normal):
  props = pyluxcore.Properties()
  props.SetFromString("""
      scene.materials.{name}.matte = clear
      scene.materials.{name}.kd = 1.0 0.0 0.0
    """.format(name="normal"))
  scene.Parse(props)
  face = np.array([verts[face[i]] for i in range(3)], dtype=float)
  r = face.mean(axis=0)
  p = r + normal
  rs = (face + 9*r) / 10
  vertices = [tuple(r.tolist()) for r in rs] + [tuple(p.tolist())]
  faces = [
    (0, 1, 2),
    (0, 1, 3),
    (1, 2, 3),
    (2, 0, 3),
  ]
  name = "normal_"+str(np.random.randint(0, 9999999))
  scene.DefineMesh(name, vertices, faces, None, None, None, None, None)
  add_object(scene, name, name, "normal", True)

def build_vertex_normals(scene, verts, normals):
  props = pyluxcore.Properties()
  props.SetFromString("""
      scene.materials.{name}.matte = clear
      scene.materials.{name}.kd = 1.0 0.0 0.0
    """.format(name="normal"))
  scene.Parse(props)
  r0 = verts + np.array([0.01, 0., 0.])
  r1 = verts + np.array([0., 0.01, 0.])
  r2 = verts + np.array([0., 0., 0.01])
  p = verts + normals
  vertices = [tuple(x.tolist()) for x in np.stack([p, r0, r1, r2], axis=1).reshape(-1,3)]
  faces = []
  for i in range(len(verts)):
    o = 4*i
    faces.append((o+0,o+1,o+2))
    faces.append((o+0,o+2,o+3))
    faces.append((o+0,o+3,o+1))
  name = "normal_"+str(np.random.randint(0, 9999999))
  scene.DefineMesh(name, vertices, faces, None, None, None, None, None)
  add_object(scene, name, name, "normal", True)

def build_session(scene, size=100, engine="PATHCPU", spp=0, tone_scale=0, contour_max=0, irradiance=False, image_path=None, model_dir=None):
  config_props = pyluxcore.Properties()
  if model_dir :
    props_string = "renderengine.type = FILESAVER"
  else:
    props_string = "renderengine.type = " + engine
  if engine == "PATHCPU":
    props_string += """
          sampler.type = SOBOL"""
  elif engine == "TILEPATHCPU":
    props_string += """
          sampler.type = TILEPATHSAMPLER
          tilepath.sampling.aa.size = 3
          tile.multipass.enable = 0"""
  else:
    raise ValueError
  if model_dir:
    props_string += """
          filesaver.directory = """ + model_dir + """
          filesaver.renderengine.type = """ + engine
  if spp > 0:
    props_string += """
          batch.haltspp = 50"""
  props_string += """
        renderengine.seed = 11
        path.pathdepth.total = 20
        path.pathdepth.diffuse = 20
        path.pathdepth.glossy = 20
        path.pathdepth.specular = 20
        path.russianroulette.depth = 99
        path.russianroulette.cap = 0.
        #lightstrategy.type = POWER
        film.width = """ + str(size) + """
        film.height = """ + str(size)
  if tone_scale == 0:
      props_string += """
            film.imagepipelines.0.0.type = TONEMAP_AUTOLINEAR"""
  else:
      props_string += """
            film.imagepipelines.0.0.type = TONEMAP_LINEAR
            film.imagepipelines.0.0.scale = """ + str(tone_scale)
  props_string += """
        film.imagepipelines.0.1.type = GAMMA_CORRECTION
        film.imagepipelines.0.1.value = 2.2
        film.outputs.0.type = RGB_IMAGEPIPELINE
        film.outputs.0.filename = """ + image_path + """_rgb.png
        film.outputs.0.index = 0"""
  if contour_max > 0:
    props_string += """
          film.imagepipelines.1.0.type = TONEMAP_LINEAR
          film.imagepipelines.1.0.scale = 5e-5
          film.imagepipelines.1.1.type = CONTOUR_LINES
          #film.imagepipelines.1.1.scale = 3e-1
          film.imagepipelines.1.1.range = """ + str(179 * contour_max) + """
          film.imagepipelines.1.1.steps = 10
          film.imagepipelines.1.1.zerogridsize = 8
          film.imagepipelines.1.2.type = GAMMA_CORRECTION
          film.imagepipelines.1.2.value = 2.2
          film.outputs.1.type = RGB_IMAGEPIPELINE
          film.outputs.1.filename = """ + image_path + """_contour.png
          film.outputs.1.index = 1"""
  if contour_max > 0 or irradiance:
    props_string += """
          film.outputs.2.type = IRRADIANCE
          film.outputs.2.filename = """ + image_path + """_irradiance.hdr
          """
  config_props.SetFromString(props_string)
  renderconfig = pyluxcore.RenderConfig(config_props, scene)
  session = pyluxcore.RenderSession(renderconfig)
  return session

def render(scene, size=100, engine="PATHCPU", spp=0, timeout=0, progress=0, tone_scale=0, contour_max=0, irradiance=False, image_path=None, model_dir=None):
  session = build_session(scene, size, engine, spp, tone_scale, contour_max, irradiance, image_path, model_dir)
  session.Start()
  if spp or engine=="TILEPATHCPU":
    sleep_time = progress if progress else 1
  else:
    assert timeout > 0
    sleep_time = progress if progress else timeout
    timeout = time.time() + timeout
  while not session.HasDone():
    sleep(sleep_time)
    session.UpdateStats()
    stats = session.GetStats()
    if progress:
      print("[Elapsed time: %3dsec][Samples %4d][Avg. samples/sec % 3.2fM on %.1fK tris]" % (
        stats.Get("stats.renderengine.time").GetFloat(),
        stats.Get("stats.renderengine.pass").GetInt(),
        (stats.Get("stats.renderengine.total.samplesec").GetFloat() / 1000000.0),
        (stats.Get("stats.dataset.trianglecount").GetFloat())))# / 1000.0)))
      print(stats)
    if timeout and time.time() > timeout:
      break
  session.Stop()

  if image_path and not model_dir:
      session.GetFilm().Save()
  if irradiance:
    pixels = session.GetFilm().GetWidth()
    buffer = array.array("f", [0.0]) * (pixels * pixels * 3)
    session.GetFilm().GetOutputFloat(pyluxcore.FilmOutputType.IRRADIANCE, buffer, 1)
    irradiance_npa = np.array(buffer).reshape(pixels, pixels, 3)
    if image_path and not model_dir:
      print("IRRADIANCE mean:{} max:{}".format(signal.medfilt(irradiance_npa).mean(), signal.medfilt(irradiance_npa).max()))
      imageio.imwrite(image_path + "_irradiance.png", irradiance_npa[::-1])
  else:
    irradiance_npa = None

  return session, irradiance_npa
