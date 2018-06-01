import os
import sys
PROJECT_ROOT = '/home/mick/dev/pyluxcore_test'
sys.path.append(os.path.join(PROJECT_ROOT, 'lib'))
import pyluxcore
import glob

from luxcore import add_object, define_mesh, render


# control whether to generate cfg&scn&ply or render images
GENERATE_MODEL = True


def main():
  pyluxcore.Init()
  scene = pyluxcore.Scene()

  props = pyluxcore.Properties()
  if False:
    props.SetFromString("""
      scene.volumes.vol_air.type = clear
      scene.volumes.vol_air.absorption = 0.0 0.0 0.0
      scene.volumes.vol_air.asymmetry = 0.0 0.0 0.0
      scene.world.volume.default = vol_air
    """)
  else:
    props.SetFromString("""
      scene.volumes.vol_air.type = homogeneous
      scene.volumes.vol_air.multiscattering = 0
      scene.volumes.vol_air.scattering = 0.001 0.001 0.001
      scene.volumes.vol_air.absorption = 0. 0. 0.
      scene.volumes.vol_air.asymmetry = 0.0 0.0 0.0
      scene.world.volume.default = vol_air
    """)
  scene.Parse(props)

  prism_vol = "lens_vol"
  props = pyluxcore.Properties()
  # props.Set(pyluxcore.Property("scene.volumes."+prism_vol+".type", "homogeneous"))
  # props.Set(pyluxcore.Property("scene.volumes."+prism_vol+".scattering", [0.01, 0, 0]))
  # props.Set(pyluxcore.Property("scene.volumes."+prism_vol+".multiscattering", 0))

  props.Set(pyluxcore.Property("scene.volumes."+prism_vol+".type", "clear"))
  props.Set(pyluxcore.Property("scene.volumes."+prism_vol+".absorption", [0,0,0]))
  props.Set(pyluxcore.Property("scene.volumes."+prism_vol+".ior", 1.4580))
  #props.Set(pyluxcore.Property("scene.volumes."+prism_vol+".priority", 255))
  scene.Parse(props)

  prism_mat = "lens"
  props = pyluxcore.Properties()
  props.Set(pyluxcore.Property("scene.materials."+prism_mat+".type", "glass"))
  props.Set(pyluxcore.Property("scene.materials."+prism_mat+".kt", [0.5, 0.5, 0.5]))
  props.Set(pyluxcore.Property("scene.materials."+prism_mat+".kr", [0.2, 0.2, 0.2]))
  props.Set(pyluxcore.Property("scene.materials."+prism_mat+".transparency", 0.5))
  # props.Set(pyluxcore.Property("scene.materials."+prism_mat+".interiorior", 1.5))
  # props.Set(pyluxcore.Property("scene.materials."+prism_mat+".exteriorior", 1.0))
  props.Set(pyluxcore.Property("scene.materials."+prism_mat+".volume.interior", prism_vol))
  props.Set(pyluxcore.Property("scene.materials."+prism_mat+".cauchyc", 0.00354))
  scene.Parse(props)

  vertices = [
    (-1, -1, 0),
    (1, -1, 0),
    (0, 0.41, 0),

    (-1, -1, 0),
    (1, -1, 0),
    (-1, -1, 2),
    (1, -1, 2),

    (1, -1, 0),
    (0, 0.41, 0),
    (1, -1, 2),
    (0, 0.41, 2),

    (0, 0.41, 0),
    (-1, -1, 0),
    (0, 0.41, 2),
    (-1, -1, 2),

    (-1, -1, 2),
    (1, -1, 2),
    (0, 0.41, 2),
  ]
  faces = [
    (0, 2, 1),

    (3, 4, 5),
    (4, 6, 5),

    (7, 8, 9),
    (8, 10, 9),

    (11, 12, 13),
    (12, 14, 13),

    (15, 16, 17),
  ]
  # vertices = [
  #   (-1, -1, -0.2),
  #   (1, -1, -0.2),
  #   (0, 0.41, -0.2),
  #
  #   (-1, -1, 0),
  #   (1, -1, 0),
  #   (-1, -1, 2),
  #   (1, -1, 2),
  #
  #   (1, -1, 0),
  #   (0, 0.41, 0),
  #   (1, -1, 2),
  #   (0, 0.41, 2),
  #
  #   (-1, -1, 0),
  #   (-1, -1, 2),
  #
  #   (-1, -1, 2.2),
  #   (1, -1, 2.2),
  #   (0, 0.41, 2.2),
  # ]
  # faces = [
  #   (0, 2, 1),
  #
  #   (3, 4, 5),
  #   (4, 6, 5),
  #
  #   (7, 8, 9),
  #   (8, 10, 9),
  #
  #   # (11, 12, 13),
  #   # (12, 14, 13),
  #   (8, 11, 12),
  #   (12, 10, 8),
  #
  #   (13, 14, 15),
  # ]
  prism = (vertices, faces)

  name = "lens0"
  define_mesh(scene, name, prism[0], prism[1], build_normals=GENERATE_MODEL)
  add_object(scene, name, name, prism_mat, visible=True)

  name = "background"
  obj_props = pyluxcore.Properties()
  obj_props.SetFromString("""
        scene.materials.{name}.type = matte
        scene.materials.{name}.kd = 0.5 0.5 0.5
        """.format(name=name))
  scene.Parse(obj_props)
  vertices = [
    (-10, 4, -20),
    (10, 0, -20),
    (10, 0, 10),
    (-10, 4, 10)
  ]
  faces = [
    (0, 1, 2),
    (2, 3, 0)
  ]
  scene.DefineMesh(name, vertices, faces, None, None, None, None, None)
  add_object(scene, name, name, name, True)

  props = pyluxcore.Properties()
  props.SetFromString("""
    scene.camera.lookat.orig = 0 -4 9.2
    scene.camera.lookat.target = 0 2 1
    scene.camera.up = 0 0 1
  """)
  scene.Parse(props)

  # """)
  # scene.Parse(props)
  props = pyluxcore.Properties()
  props.SetFromString("""
    scene.lights.l.type = laser
    scene.lights.l.position = -0.5 -5 1
    scene.lights.l.target = 0 7 1
    scene.lights.l.radius = 1.1
    # scene.lights.l.coneangle = 15
    # scene.lights.l.conedeltaangle = 1
    scene.lights.l.gain = 2000.0 2000.0 2000.0
    # scene.lights.l2.type = spot
    # scene.lights.l2.position = 0 0 10
    # scene.lights.l2.target = 0 0 0
    # scene.lights.l2.coneangle = 90
    # # scene.lights.l2.conedeltaangle = 1
    # scene.lights.l2.gain = 20.0 20.0 20.0
    scene.lights.l2.type = sky2
    scene.lights.l2.gain = 0.0003 0.0003 0.0003
  """)
  scene.Parse(props)

  image_path = os.path.join(PROJECT_ROOT, 'output/images/image')
  if GENERATE_MODEL:
    model_dir = os.path.join(PROJECT_ROOT, 'output/model')
    for f in glob.glob(os.path.join(model_dir, "*")):
      os.remove(f)
  else:
    for f in glob.glob(image_path + "_*"):
      os.remove(f)
  render(scene, size=800, engine="PATHCPU", spp=0, timeout=3, progress=3, tone_scale=0, contour_max=650, irradiance=True,
         image_path=image_path,
         model_dir=model_dir if GENERATE_MODEL else None
         )

if __name__ == "__main__":
  main()
