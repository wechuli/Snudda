# Visualises neurons and the location of the synapses connecting them.
# Tested using Blender 2.93. Should not be used with older version of Blender.

import bpy
import os
import mathutils
import numpy as np
from snudda.utils.load import SnuddaLoad
from snudda.utils.snudda_path import snudda_parse_path


class VisualiseNetwork2(object):

    # You need to provide neuron
    def __init__(self, network_path, blender_save_file=None, blender_output_image=None,
                 network_json=None, spike_file_name=None):

        self.network_path = network_path

        if network_json:
            self.network_json = network_json
            self.network_file = None
        else:
            self.network_json = None
            self.network_file = os.path.join(network_path, "network-synapses.hdf5")

        if blender_save_file:
            self.blender_save_file = blender_save_file
        else:
            self.blender_save_file = os.path.join(network_path, "visualise-network.blend")

        self.blender_output_image = blender_output_image
        
         if spike_file_name:
            spikes = np.loadtxt(spike_file_name, delimiter="\t")        ###The way the spike output files are set up currently one must read all the spikes in the network, even if only visualising a subset
            spike_times_total = spikes[:, 0] / 1e3
            spikes_neuron_id = spikes[:, 1].astype(int)
            spikedict = dict()
            neuron_ids = np.unique(spikes_neuron_id)
            for neuron_id in neuron_ids:
                idx = np.where(spike_neuron_id == neuron_id)
                neuron_spike_time = spike_times_total[idx]
                spikedict[str(neuron_id)] = neuron_spike_time
            self.spike_times = spikedict
        else:
            self.spike_times = None
        self.neuron_cache = dict([])

        # Load the neuron positions
        if self.network_file:
            self.sl = SnuddaLoad(self.network_file)
            self.data = self.sl.data
        elif self.network_json:
            from snudda.utils.fake_load import FakeLoad
            self.sl = FakeLoad()
            self.sl.import_json(self.network_json)
            self.data = self.sl.data

    def visualise(self, neuron_id=None, blender_output_image=None, white_background=True,
                  show_synapses=True):

        if neuron_id:
            neurons = [self.data["neurons"][x] for x in neuron_id]
        else:
            neurons = self.data["neurons"]
            neuron_id = self.data["neuronID"]

        if blender_output_image:
            self.blender_output_image = blender_output_image

        origo = self.data["simulationOrigo"]
        voxel_size = self.data["voxelSize"]

        # Remove the start cube
        VisualiseNetwork2.clean_scene()

        bpy.data.scenes['Scene'].render.engine = 'CYCLES'
        world = bpy.data.worlds['World']
        world.use_nodes = True

        # changing these values does affect the render.
        bg = world.node_tree.nodes['Background']
        if white_background:  # Set to True for white background
            bg.inputs[0].default_value[:3] = (1.0, 1.0, 1.0)
            bg.inputs[1].default_value = 1.0
        else:
            bg.inputs[0].default_value[:3] = (0.0, 0.0, 0.0)
            bg.inputs[1].default_value = 0.0

        # Define materials
        mat_msd1 = bpy.data.materials.new("PKHG")
        mat_msd1.diffuse_color = (77. / 255, 151. / 255, 1.0, 0.5)
        mat_msd2 = bpy.data.materials.new("PKHG")
        mat_msd2.diffuse_color = (67. / 255, 55. / 255, 181. / 255, 0.5)
        mat_fs = bpy.data.materials.new("PKHG")
        mat_fs.diffuse_color = (6. / 255, 31. / 255, 85. / 255, 1.0)
        mat_chin = bpy.data.materials.new("PKHG")
        mat_chin.diffuse_color = (252. / 255, 102. / 255, 0.0, 1.0)
        mat_lts = bpy.data.materials.new("PKHG")
        mat_lts.diffuse_color = (150. / 255, 63. / 255, 212. / 255, 1.0)
        mat_SNr = bpy.data.materials.new("PKHG")
        mat_SNr.diffuse_color = (200. / 255, 50. / 255, 50. / 255, 1.0)
        mat_other = bpy.data.materials.new("PKHG")
        mat_other.diffuse_color = (0.4, 0.4, 0.4, 1.0)

        mat_synapse = bpy.data.materials.new("PKHG")

        material_lookup = { "dspn": mat_msd1,
                            "ispn": mat_msd2,
                            "fsn": mat_fs,
                            "fs": mat_fs,
                            "chin": mat_chin,
                            "lts": mat_lts,
                            "SNr": mat_SNr,
                            "synapse": mat_synapse,
                            "other": mat_other}

        if white_background:
            mat_synapse.diffuse_color = (0.8, 0.0, 0.0, 1.0)
        else:
            mat_synapse.diffuse_color = (1.0, 1.0, 0.9, 1.0)

        # matSynapse.use_transparency = True
        mat_synapse.use_nodes = True

        if not white_background:
            emission_strength = 5.0

            # Make synapses glow
            emission = mat_synapse.node_tree.nodes.new('ShaderNodeEmission')
            emission.inputs['Strength'].default_value = emission_strength

            material_output = mat_synapse.node_tree.nodes.get('Material Output')
            mat_synapse.node_tree.links.new(material_output.inputs[0], emission.outputs[0])

        for neuron in neurons:

            e_rot = mathutils.Matrix(neuron["rotation"].reshape(3, 3)).to_euler()

            if neuron["name"] in self.neuron_cache:
                # If we already have the object in memory, copy it.
                obj = self.neuron_cache[neuron["name"]].copy()

                if self.neuron_cache[neuron["name"]].data:
                    obj.data = self.neuron_cache[neuron["name"]].data.copy()

                VisualiseNetwork2.copy_children(self.neuron_cache[neuron["name"]], obj)
                obj.animation_data_clear()

                # Will return None if there is no obj named CUBe
                obj.name = f"{neuron['name']}-{neuron['neuronID']}"
                VisualiseNetwork2.link_object(obj)
            else:
                VisualiseNetwork2.read_swc_data(snudda_parse_path(neuron["morphology"]))
                obj = bpy.context.selected_objects[0]
                obj.name = f"{neuron['name']}-{neuron['neuronID']}"

                self.neuron_cache[neuron["name"]] = obj

            obj.rotation_euler = e_rot
            scale=1000
            print(f"Setting neuron {neuron['neuronID']} ({neuron['name']}) position: {neuron['position'] * scale}")
            obj.location = neuron["position"] * scale

            n_type = neuron["type"].lower()
            if n_type in material_lookup:
                mat = material_lookup[n_type]
            else:
                mat = material_lookup["other"]
                
            if self.spike_times:
                rest_color = mat.diffuse_color[:]
                mat_spikes= bpy.data.materials.new("PKHG")                                          ###if animating spike times we need to make a fresh material per neuron
                mat_spikes.diffuse_color = rest_color
                mat_spikes.keyframe_insert(data_path="diffuse_color", frame=1.0, index=-1)
                if str(neuron['neuronID']) in self.spike_times.keys():
                    spikes = self.spike_times[str(neuron['neuronID'])]
                    spikeframes = np.round(100*np.array(spikes))                                     ###convert 'time' to Blender frames; factor of ~100 works nicely
                    for t in spikeframes:
                        mat_spikes.diffuse_color = rest_color
                        mat_spikes.keyframe_insert(data_path="diffuse_color", frame=t - 1, index=-1) ###need to add an instruction to remain at rest colour at a pre-spike time 
                        mat_spikes.diffuse_color = (1,1,1,1)                                         ###so that the colour change is not gradual but quasi-instantaneous
                        mat_spikes.keyframe_insert(data_path="diffuse_color", frame=t, index=-1) 
                        mat_spikes.diffuse_color = rest_color
                        mat_spikes.keyframe_insert(data_path="diffuse_color", frame=t + 5, index=-1)  ###change back to rest colour
                print("Color......")
                for ch in obj.children:
                    ch.active_material = mat_spikes
            else:   
                print("Color......")
                for ch in obj.children:
                    ch.active_material = mat

            obj.select_set(False)

        if show_synapses:
            print("Adding synapses...")

            # Draw the synapses
            n_synapses = 0

            for ob in bpy.context.selected_objects:
                ob.select_set(False)
            synapse_obj = None

            for vis_pre_id in neuron_id:
                for vis_post_id in neuron_id:
                    synapses, synapse_coords = self.sl.find_synapses(pre_id=vis_pre_id, post_id=vis_post_id)

                    if synapses is None:
                        # No synapses between pair
                        continue

                    for syn in synapses:
                        pre_id = syn[0]
                        post_id = syn[1]

                        assert pre_id == vis_pre_id and post_id == vis_post_id  # Just sanity check, should be true

                        # Draw this neuron (the SWC import scales from micrometers to mm), the
                        # positions in the simulation are in meters, need to scale it to mm for
                        # blender to have same units.
                        x = (origo[0] + voxel_size * syn[2]) * scale
                        y = (origo[1] + voxel_size * syn[3]) * scale
                        z = (origo[2] + voxel_size * syn[4]) * scale

                        if synapse_obj:
                            obj = synapse_obj.copy()
                            if synapse_obj.data:
                                obj.data = synapse_obj.data.copy()
                            obj.animation_data_clear()
                            obj.location = (x, y, z)
                            obj.name = f"synapse-{n_synapses}"
                            VisualiseNetwork2.link_object(obj)

                        else:
                            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.001 * 4,location=(x, y, z), scale=(1, 1, 1))
                            obj = bpy.context.selected_objects[0]
                            obj.active_material = mat_synapse
                            obj.select_set(False)
                            synapse_obj = obj

                        n_synapses += 1

                        # print(f"Added synapse #{n_synapses} at {[x, y, z]}")
                        if n_synapses % 5000 == 0:
                            print(f"Synapses added so far: {n_synapses}")

            print(f"nSynapses = {n_synapses}")

        # Add a light source
        #Commented out for now. Might want to add it later.

        #lamp_data = bpy.data.lamps.new(name="Sun", type='SUN')
        #lamp_object=bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(10.0, 10.0, 10.0), scale=(1, 1, 1))

        #lamp_object = bpy.data.objects.new(name="Sun", object_data=lamp_data)
        #bpy.context.scene.objects.link(lamp_object)

        # Place lamp to a specified location
        #lamp_object.location = (1000.0, 1000.0, 1000.0)

        # Reposition camera
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(2.98,2.68,4.96),rotation=(1.59,0,-0.26), scale=(1, 1, 1))
        cam = bpy.data.objects["Camera"]
        print(bpy.context.selected_objects)
        bpy.context.scene.camera=cam

        bpy.ops.wm.save_as_mainfile(filepath=self.blender_save_file)

        if self.blender_output_image:
            #When testing (e.g. adjuting camera position) you can skip this and just look at the blender file directly
            print("Rendering image.")
            bpy.ops.render.render()
            bpy.data.images['Render Result'].save_render(filepath=self.blender_output_image)

    @staticmethod
    def copy_children(parent, parent_copy):
        for child in parent.children:
            child_copy = child.copy()
            child_copy.parent = parent_copy
            VisualiseNetwork2.link_object(child_copy)
            VisualiseNetwork2.copy_children(child, child_copy)

    @staticmethod
    def link_object(obj):
        try:
            bpy.context.collection.objects.link(obj)
        except:
            print("Blender 2.8 failed. Likely due to 2.7 syntax.")
            #bpy.context.scene.objects.link(obj)  # Blender 2.7

    @staticmethod
    def clean_scene():
        # TODO: This does not seem to remove everything. Had some leftover synapses present still in notebook.
        print("Cleaning the scene.")
        del_list = bpy.context.copy()
        del_list['selected_objects'] = list(bpy.context.scene.objects)
        bpy.ops.object.delete(del_list)

    @staticmethod
    def read_swc_data(filepath):
        scale_f = 1000   # factor to downscale the data
        ''' read swc file '''
        print(filepath)
        f = open(filepath)
        lines = f.readlines()
        f.close()

        ''' find starting point '''
        x = 0
        while lines[x][0] == '#':
            x += 1

        ''' Create a dictionary with the first item '''
        data = lines[x].strip().split(' ')
        somaID = int(data[0])
        somaType = float(data[1])
        somaX = float(data[2])
        somaY = float(data[3])
        somaZ = float(data[4])
        somaR = float(data[5])
        somaParent = int(data[6])

        # We centre the neuron
        neuron = {somaID: [somaType, 0.0, 0.0, 0.0, somaR, somaParent]}
        x += 1

        ''' Read the rest of the lines to the dictionary '''
        for l in lines[x:]:
            data = l.strip().split(' ')
            compID = int(data[0])
            compType = float(data[1])
            compX = float(data[2])
            compY = float(data[3])
            compZ = float(data[4])
            compR = float(data[5])
            compParent = int(data[6])

            # Centre neuron, so soma is at 0,0,0
            neuron[compID] = [compType, compX - somaX, compY - somaY, compZ - somaZ, compR, compParent]

        bpy.ops.object.empty_add(type='ARROWS',
                                 location=(neuron[1][1] / scale_f, neuron[1][2] / scale_f, neuron[1][3] / scale_f),
                                 rotation=(0, 0, 0))
        a = bpy.context.selected_objects[0]
        a.name = 'neuron_swc'

        last = -10.0

        ''' Create object '''
        for key, value in neuron.items():

            if (value[0] == 1):
                # This is the soma, add it
                somaRadie = value[-2]
                bpy.ops.mesh.primitive_uv_sphere_add(
                    location=(value[1] / scale_f, value[2] / scale_f, value[3] / scale_f), radius=somaRadie / scale_f)
                # bpy.ops.mesh.primitive_uv_sphere_add(location=(value[1],value[2], value[3]),scale=(scale_f,scale_f,scale_f), radius=somaRadie)
                somaObj = bpy.context.selected_objects[0]
                somaObj.parent = a

                print("Adding soma " + str(value))

            if value[-1] == -1:
                continue

            if value[0] == 10:
                continue

            # if we need to start a new bezier curve
            if (value[-1] != last):
                # trace the origins
                tracer = bpy.data.curves.new('tracer', 'CURVE')
                tracer.dimensions = '3D'
                spline = tracer.splines.new('BEZIER')

                curve = bpy.data.objects.new('curve', tracer)
                curve.data.use_fill_caps = True  # Added 2019-06-17

                bpy.context.scene.collection.objects.link(curve)

                # render ready curve
                tracer.resolution_u = 8
                tracer.bevel_resolution = 8  # Set bevel resolution from Panel options
                tracer.fill_mode = 'FULL'
                tracer.bevel_depth = 1.0  # 0.001 # Set bevel depth from Panel options --- THIS REPLACES scale_f when setting radius

                # move nodes to objects
                p = spline.bezier_points[0]
                p.co = [neuron[value[-1]][1] / scale_f, neuron[value[-1]][2] / scale_f, neuron[value[-1]][3] / scale_f]
                # !!! Fixed a radie bug, was [5] should be [4] -- the first column is already removed /Johannes
                p.radius = neuron[value[-1]][4] / scale_f
                p.handle_right_type = 'VECTOR'
                p.handle_left_type = 'VECTOR'

                # import pdb
                # pdb.set_trace()

                if (last > 0):
                    spline.bezier_points.add(1)
                    p = spline.bezier_points[-1]
                    p.co = [value[1] / scale_f, value[2] / scale_f, value[3] / scale_f]
                    # !!! Fixed a radie bug, was [5] should be [4]
                    p.radius = value[4] / scale_f
                    p.handle_right_type = 'VECTOR'
                    p.handle_left_type = 'VECTOR'

                curve.parent = a

            # if we can continue the last bezier curve
            if value[-1] == last:
                spline.bezier_points.add(1)
                p = spline.bezier_points[-1]
                p.co = [value[1] / scale_f, value[2] / scale_f, value[3] / scale_f]
                # !!! Fixed a radie bug, was [5] should be [4]
                p.radius = value[4] / scale_f
                p.handle_right_type = 'VECTOR'
                p.handle_left_type = 'VECTOR'

            last = key

        #a.select = True
        a.select_set(True)

        return {'FINISHED'}
