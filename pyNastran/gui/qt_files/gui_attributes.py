"""
defines GuiAttributes, which defines Gui getter/setter methods
and is inherited from many GUI classes
"""
from __future__ import print_function
import os
import sys
import traceback
import time as time_module
from collections import OrderedDict

from six import string_types, iteritems, itervalues

import numpy as np
import vtk

from pyNastran.gui.gui_objects.settings import Settings

from pyNastran.gui.qt_files.tool_actions import ToolActions
from pyNastran.gui.qt_files.view_actions import ViewActions
from pyNastran.gui.qt_files.group_actions import GroupActions
from pyNastran.gui.qt_files.mouse_actions import MouseActions

from pyNastran.gui.utils.load_results import load_csv, load_deflection_csv
from pyNastran.gui.utils.load_results import create_res_obj
from pyNastran.gui.utils.vtk.vtk_utils import (
    numpy_to_vtk_points, create_vtk_cells_of_constant_element_type)

from pyNastran.bdf.cards.base_card import deprecated
from pyNastran.utils import print_bad_path


class GuiAttributes(object):
    """All methods in this class must not require VTK"""
    def __init__(self, **kwds):
        """
        These variables are common between the GUI and
        the batch mode testing that fakes the GUI
        """
        inputs = kwds['inputs']
        res_widget = kwds['res_widget']
        self.dev = False
        self.settings = Settings(self)
        self.tool_actions = ToolActions(self)
        self.view_actions = ViewActions(self)
        self.group_actions = GroupActions(self)
        self.mouse_actions = MouseActions(self)

        self.fmts = []
        self.glyph_scale_factor = 1.0
        self.html_logging = False
        self.format_class_map = {}

        # the result type being currently shown
        # for a Nastran NodeID/displacement, this is 'node'
        # for a Nastran ElementID/PropertyID, this is 'element'
        self.result_location = None

        self.case_keys = []
        self.res_widget = res_widget
        self._show_flag = True
        self.observers = {}

        if 'test' in inputs:
            self.is_testing_flag = inputs['test']
        else:
            self.is_testing_flag = False
        self.is_groups = False
        self._logo = None
        self._script_path = None
        self._icon_path = ''

        self.title = None
        self.min_value = None
        self.max_value = None
        self.blue_to_red = False
        self._is_axes_shown = True
        self.nvalues = 9
        #-------------

        # window variables
        self._legend_window_shown = False
        self._preferences_window_shown = False
        self._clipping_window_shown = False
        self._edit_geometry_properties_window_shown = False
        self._modify_groups_window_shown = False
        #self._label_window = None
        #-------------
        # inputs dict
        self.is_edges = False
        self.is_edges_black = self.is_edges

        #self.format = ''
        debug = inputs['debug']
        self.debug = debug
        assert debug in [True, False], 'debug=%s' % debug

        #-------------
        # file
        self.menu_bar_format = None
        self.format = None
        self.infile_name = None
        self.out_filename = None
        self.dirname = ''
        self.last_dir = '' # last visited directory while opening file
        self._default_python_file = None

        #-------------
        # internal params
        self.ncases = 0
        self.icase = 0
        self.icase_disp = None
        self.icase_vector = None
        self.icase_fringe = None

        self.nnodes = 0
        self.nelements = 0

        self.supported_formats = []
        self.model_type = None

        self.tools = []
        self.checkables = []
        self.actions = {}
        self.modules = OrderedDict()

        # actor_slots
        self.text_actors = {}
        self.geometry_actors = OrderedDict()
        self.alt_grids = {} #additional grids

        # coords
        self.transform = {}
        self.axes = {}

        #geom = Geom(color, line_thickness, etc.)
        #self.geometry_properties = {
        #    'name' : Geom(),
        #}
        self.geometry_properties = OrderedDict()
        self.follower_nodes = {}
        self.follower_functions = {}

        self.label_actors = {-1 : []}
        self.label_ids = {}
        self.cameras = {}
        self.label_scale = 1.0 # in percent

        self.is_horizontal_scalar_bar = False
        self.is_low_to_high = True

        self.result_cases = {}
        self.num_user_points = 0

        self._is_displaced = False
        self._is_forces = False
        self._is_fringe = False

        self._xyz_nominal = None

        self.nvalues = 9
        self.nid_maps = {}
        self.eid_maps = {}
        self.name = 'main'

        self.groups = {}
        self.group_active = 'main'

        #if not isinstance(res_widget, MockResWidget):
            #if qt_version == 4:
                #QMainWindow.__init__(self)
            #elif qt_version == 5:
                #super(QMainWindow, self).__init__()

        self.main_grids = {}
        self.main_grid_mappers = {}
        self.main_geometry_actors = {}

        self.main_edge_mappers = {}
        self.main_edge_actors = {}

        self.color_order = [
            (1.0, 0.145098039216, 1.0),
            (0.0823529411765, 0.0823529411765, 1.0),
            (0.0901960784314, 1.0, 0.941176470588),
            (0.501960784314, 1.0, 0.0941176470588),
            (1.0, 1.0, 0.117647058824),
            (1.0, 0.662745098039, 0.113725490196)
        ]

        self.color_function_black = vtk.vtkColorTransferFunction()
        self.color_function_black.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
        self.color_function_black.AddRGBPoint(1.0, 0.0, 0.0, 0.0)

    #-------------------------------------------------------------------
    # deprecated attributes
    def deprecated(self, old_name, new_name, deprecated_version):
        # type: (str, str, str, Optional[List[int]]) -> None
        """
        Throws a deprecation message and crashes if past a specific version.

        Parameters
        ----------
        old_name : str
            the old function name
        new_name : str
            the new function name
        deprecated_version : float
            the version the method was first deprecated in
        """
        deprecated(old_name, new_name, deprecated_version, levels=[0])

    @property
    def nNodes(self):
        """gets the number of nodes"""
        self.deprecated('self.nNodes', 'self.nnodes', '1.1')
        return self.nnodes

    @nNodes.setter
    def nNodes(self, nnodes):
        """sets the number of nodes"""
        self.deprecated('self.nNodes', 'self.nnodes', '1.1')
        self.nnodes = nnodes

    @property
    def nElements(self):
        """gets the number of elements"""
        self.deprecated('self.nElements', 'self.nelements', '1.1')
        return self.nelements

    @nElements.setter
    def nElements(self, nelements):
        """sets the number of elements"""
        self.deprecated('self.nElements', 'self.nelements', '1.1')
        self.nelements = nelements

    #-------------------------------------------------------------------
    # geom
    @property
    def grid(self):
        """gets the active grid"""
        #print('get grid; %r' % self.name)
        return self.main_grids[self.name]

    @grid.setter
    def grid(self, grid):
        """sets the active grid"""
        #print('set grid; %r' % self.name)
        self.main_grids[self.name] = grid

    @property
    def grid_mapper(self):
        """gets the active grid_mapper"""
        return self.main_grid_mappers[self.name]

    @grid_mapper.setter
    def grid_mapper(self, grid_mapper):
        """sets the active grid_mapper"""
        self.main_grid_mappers[self.name] = grid_mapper

    @property
    def geom_actor(self):
        """gets the active geom_actor"""
        return self.main_geometry_actors[self.name]

    @geom_actor.setter
    def geom_actor(self, geom_actor):
        """sets the active geom_actor"""
        self.main_geometry_actors[self.name] = geom_actor

    #-------------------------------------------------------------------
    # edges
    @property
    def edge_mapper(self):
        return self.main_edge_mappers[self.name]

    @edge_mapper.setter
    def edge_mapper(self, edge_mapper):
        self.main_edge_mappers[self.name] = edge_mapper

    @property
    def edge_actor(self):
        """gets the active edge_actor"""
        return self.main_edge_actors[self.name]

    @edge_actor.setter
    def edge_actor(self, edge_actor):
        """sets the active edge_actor"""
        self.main_edge_actors[self.name] = edge_actor

    def set_glyph_scale_factor(self, scale):
        """sets the glyph scale factor"""
        self.glyph_scale_factor = scale
        self.glyphs.SetScaleFactor(scale)

    @property
    def nid_map(self):
        """gets the node_id map"""
        return self.nid_maps[self.name]

    @nid_map.setter
    def nid_map(self, nid_map):
        """sets the node_id map"""
        self.nid_maps[self.name] = nid_map

    @property
    def eid_map(self):
        """gets the element_id map"""
        try:
            return self.eid_maps[self.name]
        except:
            msg = 'KeyError: key=%r; keys=%s' % (self.name, list(self.eid_maps.keys()))
            raise KeyError(msg)

    @eid_map.setter
    def eid_map(self, eid_map):
        """sets the element_id map"""
        self.eid_maps[self.name] = eid_map

    #---------------------------------------------------------------------------
    def _on_load_custom_results_load_filename(self, out_filename=None, restype=None):
        is_failed = True
        #unused_geometry_format = self.format
        if self.format is None:
            msg = 'on_load_results failed:  You need to load a file first...'
            self.log_error(msg)
            return is_failed, None, None

        if out_filename in [None, False]:
            title = 'Select a Custom Results File for %s' % (self.format)

            #print('wildcard_level =', wildcard_level)
            #self.wildcard_delimited = 'Delimited Text (*.txt; *.dat; *.csv)'
            fmts = [
                'Node - Delimited Text (*.txt; *.dat; *.csv)',
                'Element - Delimited Text (*.txt; *.dat; *.csv)',
                'Nodal Deflection - Delimited Text (*.txt; *.dat; *.csv)',
                'Patran nod (*.nod)',
            ]
            fmt = ';;'.join(fmts)
            wildcard_level, out_filename = self._create_load_file_dialog(fmt, title)
            if not out_filename:
                return is_failed, None, None # user clicked cancel
            iwildcard = fmts.index(wildcard_level)
        else:
            fmts = [
                'node', 'element', 'deflection', 'patran_nod',
            ]
            iwildcard = fmts.index(restype.lower())
        is_failed = False
        return is_failed, out_filename, iwildcard

    def on_load_custom_results(self, out_filename=None, restype=None):
        """will be a more generalized results reader"""
        is_failed, out_filename, iwildcard = self._on_load_custom_results_load_filename(
            out_filename=out_filename, restype=restype)

        if is_failed:
            return is_failed
        if out_filename == '':
            is_failed = True
            return is_failed

        is_failed = True
        if not os.path.exists(out_filename):
            msg = 'result file=%r does not exist' % out_filename
            self.log_error(msg)
            return is_failed

        try:
            if iwildcard == 0:
                self._on_load_nodal_elemental_results('Nodal', out_filename)
                restype = 'Node'
            elif iwildcard == 1:
                self._on_load_nodal_elemental_results('Elemental', out_filename)
                restype = 'Element'
            elif iwildcard == 2:
                self._load_deflection(out_filename)
                restype = 'Deflection'
            elif iwildcard == 3:
                self._load_patran_nod(out_filename)
                restype = 'Patran_nod'
            else:
                raise NotImplementedError('iwildcard = %s' % iwildcard)
        except:
            msg = traceback.format_exc()
            self.log_error(msg)
            return is_failed
        self.log_command("on_load_custom_results(%r, restype=%r)" % (out_filename, restype))
        is_failed = False
        return is_failed

    def _load_deflection(self, out_filename):
        """loads a force file"""
        self._load_deflection_force(out_filename, is_deflection=False, is_force=True)

    def _load_deflection_force(self, out_filename, is_deflection=False, is_force=False):
        out_filename_short = os.path.basename(out_filename)
        A, fmt_dict, headers = load_deflection_csv(out_filename)
        #nrows, ncols, fmts
        header0 = headers[0]
        result0 = A[header0]
        nrows = result0.shape[0]

        assert nrows == self.nnodes, 'nrows=%s nnodes=%s' % (nrows, self.nnodes)
        result_type = 'node'
        self._add_cases_to_form(A, fmt_dict, headers, result_type,
                                out_filename_short, update=True, is_scalar=False,
                                is_deflection=is_deflection, is_force=is_deflection)

    def _on_load_nodal_elemental_results(self, result_type, out_filename=None):
        """
        Loads a CSV/TXT results file.  Must have called on_load_geometry first.

        Parameters
        ----------
        result_type : str
            'Nodal', 'Elemental'
        out_filename : str / None
            the path to the results file
        """
        try:
            self._load_csv(result_type, out_filename)
        except:
            msg = traceback.format_exc()
            self.log_error(msg)
            #return
            raise

        #if 0:
            #self.out_filename = out_filename
            #msg = '%s - %s - %s' % (self.format, self.infile_name, out_filename)
            #self.window_title = msg
            #self.out_filename = out_filename

    def _load_patran_nod(self, nod_filename):
        """reads a Patran formatted *.nod file"""
        from pyNastran.bdf.patran_utils.read_patran import load_patran_nod
        A, fmt_dict, headers = load_patran_nod(nod_filename, self.node_ids)

        out_filename_short = os.path.relpath(nod_filename)
        result_type = 'node'
        self._add_cases_to_form(A, fmt_dict, headers, result_type,
                                out_filename_short, update=True,
                                is_scalar=True)

    def _load_csv(self, result_type, out_filename):
        """
        common method between:
          - on_add_nodal_results(filename)
          - on_add_elemental_results(filename)

        Parameters
        ----------
        result_type : str
            ???
        out_filename : str
            the CSV filename to load
        """
        out_filename_short = os.path.relpath(out_filename)
        A, fmt_dict, headers = load_csv(out_filename)
        #nrows, ncols, fmts
        header0 = headers[0]
        result0 = A[header0]
        nrows = result0.size

        if result_type == 'Nodal':
            assert nrows == self.nnodes, 'nrows=%s nnodes=%s' % (nrows, self.nnodes)
            result_type2 = 'node'
            #ids = self.node_ids
        elif result_type == 'Elemental':
            assert nrows == self.nelements, 'nrows=%s nelements=%s' % (nrows, self.nelements)
            result_type2 = 'centroid'
            #ids = self.element_ids
        else:
            raise NotImplementedError('result_type=%r' % result_type)

        #num_ids = len(ids)
        #if num_ids != nrows:
            #A2 = {}
            #for key, matrix in iteritems(A):
                #fmt = fmt_dict[key]
                #assert fmt not in ['%i'], 'fmt=%r' % fmt
                #if len(matrix.shape) == 1:
                    #matrix2 = np.full(num_ids, dtype=matrix.dtype)
                    #iids = np.searchsorted(ids, )
            #A = A2
        self._add_cases_to_form(A, fmt_dict, headers, result_type2,
                                out_filename_short, update=True, is_scalar=True)

    def _add_cases_to_form(self, A, fmt_dict, headers, result_type,
                           out_filename_short, update=True, is_scalar=True,
                           is_deflection=False, is_force=False):
        """
        common method between:
          - _load_csv
          - _load_deflection_csv

        Parameters
        ----------
        A : dict[key] = (n, m) array
            the numpy arrays
            key : str
                the name
            n : int
                number of nodes/elements
            m : int
                secondary dimension
                N/A : 1D array
                3 : deflection
        fmt_dict : dict[header] = fmt
            the format of the arrays
            header : str
                the name
            fmt : str
                '%i', '%f'
        headers : List[str]???
            the titles???
        result_type : str
            'node', 'centroid'
        out_filename_short : str
            the display name
        update : bool; default=True
            update the res_widget

        # A = np.loadtxt('loadtxt_spike.txt', dtype=('float,int'))
        # dtype=[('f0', '<f8'), ('f1', '<i4')])
        # A['f0']
        # A['f1']
        """
        #print('A =', A)
        formi = []
        form = self.get_form()
        icase = len(self.case_keys)
        islot = 0
        for case_key in self.case_keys:
            if isinstance(case_key, tuple):
                islot = case_key[0]
                break

        #assert len(headers) > 0, 'headers=%s' % (headers)
        #assert len(headers) < 50, 'headers=%s' % (headers)
        for header in headers:
            if is_scalar:
                out = create_res_obj(islot, headers, header, A, fmt_dict, result_type)
            else:
                out = create_res_obj(islot, headers, header, A, fmt_dict, result_type,
                                     self.settings.dim_max, self.xyz_cid0)
            res_obj, title = out

            #cases[icase] = (stress_res, (subcase_id, 'Stress - isElementOn'))
            #form_dict[(key, itime)].append(('Stress - IsElementOn', icase, []))
            #key = (res_obj, (0, title))
            self.case_keys.append(icase)
            self.result_cases[icase] = (res_obj, (islot, title))
            formi.append((header, icase, []))

            # TODO: double check this should be a string instead of an int
            self.label_actors[icase] = []
            self.label_ids[icase] = set([])
            icase += 1
        form.append((out_filename_short, None, formi))

        self.ncases += len(headers)
        #cases[(ID, 2, 'Region', 1, 'centroid', '%i')] = regions
        if update:
            self.res_widget.update_results(form, 'main')

    #-------------------------------------------------------------------
    def set_quad_grid(self, name, nodes, elements, color, line_width=5, opacity=1.):
        """
        Makes a CQUAD4 grid
        """
        self.create_alternate_vtk_grid(name, color=color, line_width=line_width,
                                       opacity=opacity, representation='wire')

        nnodes = nodes.shape[0]
        nquads = elements.shape[0]
        #print(nodes)
        if nnodes == 0:
            return
        if nquads == 0:
            return

        #print('adding quad_grid %s; nnodes=%s nquads=%s' % (name, nnodes, nquads))
        assert isinstance(nodes, np.ndarray), type(nodes)

        points = numpy_to_vtk_points(nodes)
        grid = self.alt_grids[name]
        grid.SetPoints(points)

        etype = 9  # vtk.vtkQuad().GetCellType()
        create_vtk_cells_of_constant_element_type(grid, elements, etype)

        self._add_alt_actors({name : self.alt_grids[name]})

        #if name in self.geometry_actors:
        self.geometry_actors[name].Modified()

    def _add_alt_actors(self, grids_dict, names_to_ignore=None):
        if names_to_ignore is None:
            names_to_ignore = ['main']

        names = set(list(grids_dict.keys()))
        names_old = set(list(self.geometry_actors.keys()))
        names_old = names_old - set(names_to_ignore)
        #print('names_old1 =', names_old)

        #names_to_clear = names_old - names
        #self._remove_alt_actors(names_to_clear)
        #print('names_old2 =', names_old)
        #print('names =', names)
        for name in names:
            #print('adding %s' % name)
            grid = grids_dict[name]
            self.tool_actions._add_alt_geometry(grid, name)

    def _remove_alt_actors(self, names=None):
        if names is None:
            names = list(self.geometry_actors.keys())
            names.remove('main')
        for name in names:
            actor = self.geometry_actors[name]
            self.rend.RemoveActor(actor)
            del actor

    @property
    def displacement_scale_factor(self):
        """
        # dim_max = max_val * scale
        # scale = dim_max / max_val
        # 0.25 added just cause

        scale = self.displacement_scale_factor / tnorm_abs_max
        """
        #scale = dim_max / tnorm_abs_max * 0.25
        scale = self.settings.dim_max * 0.25
        return scale

    def set_script_path(self, script_path):
        """Sets the path to the custom script directory"""
        self._script_path = script_path

    def set_icon_path(self, icon_path):
        """
        Sets the path to the icon directory where custom icons are found
        """
        self._icon_path = icon_path

    def form(self):
        formi = self.res_widget.get_form()
        return formi

    def get_form(self):
        return self._form

    def set_form(self, formi):
        self._form = formi
        data = []
        for key in self.case_keys:
            assert isinstance(key, int), key
            unused_obj, (i, unused_name) = self.result_cases[key]
            t = (i, [])
            data.append(t)

        self.res_widget.update_results(formi, self.name)

        key = list(self.case_keys)[0]
        location = self.get_case_location(key)
        method = 'centroid' if location else 'nodal'

        data2 = [(method, None, [])]
        self.res_widget.update_methods(data2)

    def _remove_old_geometry(self, geom_filename):
        skip_reading = False
        if self.dev:
            return skip_reading

        self.eid_map = {}
        self.nid_map = {}
        params_to_delete = (
            'case_keys', 'icase', 'isubcase_name_map',
            'result_cases', 'eid_map', 'nid_map',
        )
        if geom_filename is None or geom_filename is '':
            skip_reading = True
            return skip_reading
        else:
            self.turn_text_off()
            self.grid.Reset()

            self.result_cases = OrderedDict()
            self.ncases = 0
            for param in params_to_delete:
                if hasattr(self, param):  # TODO: is this correct???
                    try:
                        delattr(self, param)
                    except AttributeError:
                        msg = 'cannot delete %r; hasattr=%r' % (param, hasattr(self, param))
                        self.log.warning(msg)

            skip_reading = False
        #self.scalarBar.VisibilityOff()
        self.scalarBar.Modified()
        return skip_reading

    #---------------------------------------------------------------------------
    def on_run_script(self, python_file=False):
        """pulldown for running a python script"""
        is_passed = False
        if python_file in [None, False]:
            title = 'Choose a Python Script to Run'
            wildcard = "Python (*.py)"
            infile_name = self._create_load_file_dialog(
                wildcard, title, self._default_python_file)[1]
            if not infile_name:
                return is_passed # user clicked cancel

            #python_file = os.path.join(script_path, infile_name)
            python_file = os.path.join(infile_name)

        if not os.path.exists(python_file):
            msg = 'python_file = %r does not exist' % python_file
            self.log_error(msg)
            return is_passed

        txt = open(python_file, 'r').read()
        is_passed = self._execute_python_code(txt, show_msg=False)
        if not is_passed:
            return is_passed
        self._default_python_file = python_file
        self.log_command('self.on_run_script(%r)' % python_file)
        print('self.on_run_script(%r)' % python_file)
        return is_passed

    def _execute_python_code(self, txt, show_msg=True):
        """executes python code"""
        is_passed = False
        if len(txt) == 0:
            return is_passed
        if show_msg:
            self.log_command(txt)
        try:
            exec(txt)
        except TypeError as error:
            self.log_error('\n' + ''.join(traceback.format_stack()))
            #traceback.print_exc(file=self.log_error)
            self.log_error(str(error))
            self.log_error(str(txt))
            self.log_error(str(type(txt)))
            return is_passed
        except Exception as error:
            #self.log_error(traceback.print_stack(f))
            self.log_error('\n' + ''.join(traceback.format_stack()))
            #traceback.print_exc(file=self.log_error)
            self.log_error(str(error))
            self.log_error(str(txt))
            return is_passed
        is_passed = True
        return is_passed

    #---------------------------------------------------------------------------
    def reset_labels(self, reset_minus1=True):
        """
        Wipe all labels and regenerate the key slots based on the case keys.
        This is used when changing the model.
        """
        self._remove_labels()

        reset_minus1 = True
        # new geometry
        if reset_minus1:
            self.label_actors = {-1 : []}
        else:
            for idi in self.label_actors:
                if idi == -1:
                    continue
                self.label_actors[idi] = []
        self.label_ids = {}

        #self.case_keys = [
            #(1, 'ElementID', 1, 'centroid', '%.0f'),
            #(1, 'Region', 1, 'centroid', '%.0f')
        #]
        for icase in self.case_keys:
            #result_name = self.get_result_name(icase)
            self.label_actors[icase] = []
            self.label_ids[icase] = set([])
        #print(self.label_actors)
        #print(self.label_ids)

    def _remove_labels(self):
        """
        Remove all labels from the current result case.
        This happens when the user explictly selects the clear label button.
        """
        if len(self.label_actors) == 0:
            self.log.warning('No actors to remove')
            return

        # existing geometry
        for icase, actors in iteritems(self.label_actors):
            if icase == -1:
                continue
            for actor in actors:
                self.rend.RemoveActor(actor)
                del actor
            self.label_actors[icase] = []
            self.label_ids[icase] = set([])

    def clear_labels(self):
        """
        This clears out all labels from all result cases.
        """
        if len(self.label_actors) == 0:
            self.log.warning('No actors to clear')
            return

        # existing geometry
        icase = self.icase

        actors = self.label_actors[icase]
        for actor in actors:
            self.rend.RemoveActor(actor)
            del actor
        self.label_actors[icase] = []
        self.label_ids[icase] = set([])

    def resize_labels(self, case_keys=None, show_msg=True):
        """
        This resizes labels for all result cases.
        TODO: not done...
        """
        if case_keys is None:
            names = 'None)  # None -> all'
            case_keys = sorted(self.label_actors.keys())
        else:
            mid = '%s,' * len(case_keys)
            names = '[' + mid[:-1] + '])'

        count = 0
        for icase in case_keys:
            actors = self.label_actors[icase]
            for actor in actors:
                actor.VisibilityOff()
                count += 1
        if count and show_msg:
            self.log_command('resize_labels(%s)' % names)

    #---------------------------------------------------------------------------
    def hide_legend(self):
        """hides the legend"""
        self.scalar_bar.VisibilityOff()
        #self.scalar_bar.is_shown = False
        if self._legend_window_shown:
            self._legend_window.hide_legend()

    def show_legend(self):
        """shows the legend"""
        self.scalar_bar.VisibilityOn()
        if self._legend_window_shown:
            self._legend_window.show_legend()
        #self.scalar_bar.is_shown = True

    def update_scalar_bar(self, title, min_value, max_value, norm_value,
                          data_format,
                          nlabels=None, labelsize=None,
                          ncolors=None, colormap=None,
                          is_shown=True):
        """
        Updates the Scalar Bar

        Parameters
        ----------
        title : str
            the scalar bar title
        min_value : float
            the blue value
        max_value :
            the red value
        data_format : str
            '%g','%f','%i', etc.
        nlabels : int (default=None -> auto)
            the number of labels
        labelsize : int (default=None -> auto)
            the label size
        ncolors : int (default=None -> auto)
            the number of colors
        colormap : varies
            str : the name
            ndarray : (N, 3) float ndarry
                red-green-blue array
        is_shown : bool
            show the scalar bar
        """
        if colormap is None:
            colormap = self.settings.colormap
        #print("update_scalar_bar min=%s max=%s norm=%s" % (min_value, max_value, norm_value))
        self.scalar_bar.update(title, min_value, max_value, norm_value, data_format,
                               nlabels=nlabels, labelsize=labelsize,
                               ncolors=ncolors, colormap=colormap,
                               is_low_to_high=self.is_low_to_high,
                               is_horizontal=self.is_horizontal_scalar_bar,
                               is_shown=is_shown)

    def on_update_scalar_bar(self, title, min_value, max_value, data_format):
        self.title = str(title)
        self.min_value = float(min_value)
        self.max_value = float(max_value)

        try:
            data_format % 1
        except:
            msg = ("failed applying the data formatter format=%r and "
                   "should be of the form: '%i', '%8f', '%.2f', '%e', etc.")
            self.log_error(msg)
            return
        #self.data_format = data_format
        self.log_command('on_update_scalar_bar(%r, %r, %r, %r)' % (
            title, min_value, max_value, data_format))

    #---------------------------------------------------------------------------
    def create_coordinate_system(self, coord_id, dim_max, label='',
                                 origin=None, matrix_3x3=None,
                                 coord_type='xyz'):
        """
        Creates a coordinate system

        Parameters
        ----------
        coord_id : float
            the coordinate system id
        dim_max : float
            the max model dimension; 10% of the max will be used for the coord length
        label : str
            the coord id or other unique label (default is empty to indicate the global frame)
        origin : (3, ) ndarray/list/tuple
            the origin
        matrix_3x3 : (3, 3) ndarray
            a standard Nastran-style coordinate system
        coord_type : str
            a string of 'xyz', 'Rtz', 'Rtp' (xyz, cylindrical, spherical)
            that changes the axis names

        .. todo::  coord_type is not supported ('xyz' ONLY)
        .. todo::  Can only set one coordinate system
        """
        self.tool_actions.create_coordinate_system(
            coord_id, dim_max, label=label,
            origin=origin, matrix_3x3=matrix_3x3,
            coord_type=coord_type)

    def create_global_axes(self, dim_max):
        """creates the global axis"""
        cid = 0
        self.tool_actions.create_coordinate_system(
            cid, dim_max, label='', origin=None, matrix_3x3=None, coord_type='xyz')

    def create_corner_axis(self):
        """creates the axes that sits in the corner"""
        self.tool_actions.create_corner_axis()

    def update_axes_length(self, dim_max):
        """
        sets the driving dimension for:
          - picking?
          - coordinate systems
          - label size
        """
        self.settings.dim_max = dim_max
        dim = self.settings.dim_max * self.settings.coord_scale
        self.on_set_axes_length(dim)

    def on_set_axes_length(self, dim=None):
        """
        scale coordinate system based on model length
        """
        if dim is None:
            dim = self.settings.dim_max * self.settings.coord_scale
        for axes in itervalues(self.axes):
            axes.SetTotalLength(dim, dim, dim)

    #---------------------------------------------------------------------------
    def on_load_geometry(self, infile_name=None, geometry_format=None, name='main',
                         plot=True, raise_error=False):
        """
        Loads a baseline geometry

        Parameters
        ----------
        infile_name : str; default=None -> popup
            path to the filename
        geometry_format : str; default=None
            the geometry format for programmatic loading
        name : str; default='main'
            the name of the actor; don't use this
        plot : bool; default=True
            Should the baseline geometry have results created and plotted/rendered?
            If you're calling the on_load_results method immediately after, set it to False
        raise_error : bool; default=True
            stop the code if True
        """
        is_failed, out = self._load_geometry_filename(
            geometry_format, infile_name)
        print("is_failed =", is_failed)
        if is_failed:
            return

        has_results = False
        infile_name, load_function, filter_index, formats, geometry_format2 = out
        if load_function is not None:
            self.last_dir = os.path.split(infile_name)[0]

            if self.name == '':
                name = 'main'
            else:
                print('name = %r' % name)

            if name != self.name:
                #scalar_range = self.grid_selected.GetScalarRange()
                #self.grid_mapper.SetScalarRange(scalar_range)
                self.grid_mapper.ScalarVisibilityOff()
                #self.grid_mapper.SetLookupTable(self.color_function)
            self.name = str(name)
            self._reset_model(name)

            # reset alt grids
            names = self.alt_grids.keys()
            for name in names:
                self.alt_grids[name].Reset()
                self.alt_grids[name].Modified()

            if not os.path.exists(infile_name) and geometry_format:
                msg = 'input file=%r does not exist' % infile_name
                self.log_error(msg)
                self.log_error(print_bad_path(infile_name))
                return

            # clear out old data
            if self.model_type is not None:
                clear_name = 'clear_' + self.model_type
                try:
                    dy_method = getattr(self, clear_name)  # 'self.clear_nastran()'
                    dy_method()
                except:
                    print("method %r does not exist" % clear_name)
            self.log_info("reading %s file %r" % (geometry_format, infile_name))

            try:
                time0 = time_module.time()

                if geometry_format2 in self.format_class_map:
                    # intialize the class
                    cls = self.format_class_map[geometry_format](self)
                    function_name = 'load_%s_geometry' % geometry_format2
                    load_function2 = getattr(cls, function_name)
                    has_results = load_function2(infile_name, name=name, plot=plot)
                else:
                    has_results = load_function(infile_name, name=name, plot=plot) # self.last_dir,

                dt = time_module.time() - time0
                print('dt_load = %.2f sec = %.2f min' % (dt, dt / 60.))
                #else:
                    #name = load_function.__name__
                    #self.log_error(str(args))
                    #self.log_error("'plot' needs to be added to %r; "
                                   #"args[-1]=%r" % (name, args[-1]))
                    #has_results = load_function(infile_name) # , self.last_dir
                    #form, cases = load_function(infile_name) # , self.last_dir
            except Exception as error:
                #raise
                msg = traceback.format_exc()
                self.log_error(msg)
                if raise_error or self.dev:
                    raise
                #return
            #self.vtk_panel.Update()
            self.rend.ResetCamera()

        # the model has been loaded, so we enable load_results
        if filter_index >= 0:
            self.format = formats[filter_index].lower()
            unused_enable = has_results
            #self.load_results.Enable(enable)
        else: # no file specified
            return
        #print("on_load_geometry(infile_name=%r, geometry_format=None)" % infile_name)
        self.infile_name = infile_name
        self.out_filename = None
        #if self.out_filename is not None:
            #msg = '%s - %s - %s' % (self.format, self.infile_name, self.out_filename)

        if name == 'main':
            msg = '%s - %s' % (self.format, self.infile_name)
            self.window_title = msg
            self.update_menu_bar()
            main_str = ''
        else:
            main_str = ', name=%r' % name

        self.log_command("on_load_geometry(infile_name=%r, geometry_format=%r%s)" % (
            infile_name, self.format, main_str))

    def _load_geometry_filename(self, geometry_format, infile_name):
        """gets the filename and format"""
        wildcard = ''
        is_failed = False

        if geometry_format and geometry_format.lower() not in self.supported_formats:
            is_failed = True
            msg = 'The import for the %r module failed.\n' % geometry_format
            self.log_error(msg)
            return is_failed, None

        if infile_name:
            if geometry_format is None:
                is_failed = True
                msg = 'infile_name=%r and geometry_format=%r; both must be specified\n' % (
                    infile_name, geometry_format)
                self.log_error(msg)
                return is_failed, None

            geometry_format = geometry_format.lower()
            print("geometry_format = %r" % geometry_format)

            for fmt in self.fmts:
                fmt_name, _major_name, _geom_wildcard, geom_func, res_wildcard, _resfunc = fmt
                if geometry_format == fmt_name:
                    load_function = geom_func
                    if res_wildcard is None:
                        unused_has_results = False
                    else:
                        unused_has_results = True
                    break
            else:
                self.log_error('---invalid format=%r' % geometry_format)
                is_failed = True
                return is_failed, None
            formats = [geometry_format]
            filter_index = 0
        else:
            # load a pyqt window
            formats = []
            load_functions = []
            has_results_list = []
            wildcard_list = []

            # setup the selectable formats
            for fmt in self.fmts:
                fmt_name, _major_name, geom_wildcard, geom_func, res_wildcard, _res_func = fmt
                formats.append(_major_name)
                wildcard_list.append(geom_wildcard)
                load_functions.append(geom_func)

                if res_wildcard is None:
                    has_results_list.append(False)
                else:
                    has_results_list.append(True)

            # the list of formats that will be selectable in some odd syntax
            # that pyqt uses
            wildcard = ';;'.join(wildcard_list)

            # get the filter index and filename
            if infile_name is not None and geometry_format is not None:
                filter_index = formats.index(geometry_format)
            else:
                title = 'Choose a Geometry File to Load'
                wildcard_index, infile_name = self._create_load_file_dialog(wildcard, title)
                if not infile_name:
                    # user clicked cancel
                    is_failed = True
                    return is_failed, None
                filter_index = wildcard_list.index(wildcard_index)

            geometry_format = formats[filter_index]
            load_function = load_functions[filter_index]
            unused_has_results = has_results_list[filter_index]
        return is_failed, (infile_name, load_function, filter_index, formats, geometry_format)

    def on_load_results(self, out_filename=None):
        """
        Loads a results file.  Must have called on_load_geometry first.

        Parameters
        ----------
        out_filename : str / None
            the path to the results file
        """
        geometry_format = self.format
        if self.format is None:
            msg = 'on_load_results failed:  You need to load a file first...'
            self.log_error(msg)
            raise RuntimeError(msg)

        if out_filename in [None, False]:
            title = 'Select a Results File for %s' % self.format
            wildcard = None
            load_function = None

            for fmt in self.fmts:
                print(fmt)
                fmt_name, _major_name, _geowild, _geofunc, _reswild, _resfunc = fmt
                if geometry_format == fmt_name:
                    wildcard = _reswild
                    load_function = _resfunc
                    break
            else:
                msg = 'format=%r is not supported' % geometry_format
                self.log_error(msg)
                raise RuntimeError(msg)

            if wildcard is None:
                msg = 'format=%r has no method to load results' % geometry_format
                self.log_error(msg)
                return
            out_filename = self._create_load_file_dialog(wildcard, title)[1]
        else:

            for fmt in self.fmts:
                fmt_name, _major_name, _geowild, _geofunc, _reswild, _resfunc = fmt
                #print('fmt_name=%r geometry_format=%r' % (fmt_name, geometry_format))
                if fmt_name == geometry_format:
                    load_function = _resfunc
                    break
            else:
                msg = ('format=%r is not supported.  '
                       'Did you load a geometry model?' % geometry_format)
                self.log_error(msg)
                raise RuntimeError(msg)

        if out_filename == '':
            return
        if isinstance(out_filename, string_types):
            out_filename = [out_filename]
        for out_filenamei in out_filename:
            if not os.path.exists(out_filenamei):
                msg = 'result file=%r does not exist' % out_filenamei
                self.log_error(msg)
                return
                #raise IOError(msg)
            self.last_dir = os.path.split(out_filenamei)[0]

            try:
                load_function(out_filenamei)
            except: #  as e
                msg = traceback.format_exc()
                self.log_error(msg)
                print(msg)
                #return
                raise

            self.out_filename = out_filenamei
            msg = '%s - %s - %s' % (self.format, self.infile_name, out_filenamei)
            self.window_title = msg
            print("on_load_results(%r)" % out_filenamei)
            self.out_filename = out_filenamei
            self.log_command("on_load_results(%r)" % out_filenamei)

    @property
    def window_title(self):
        return self.getWindowTitle()

    @window_title.setter
    def window_title(self, msg):
        #msg2 = "%s - "  % self.base_window_title
        #msg2 += msg
        self.setWindowTitle(msg)

    def build_fmts(self, fmt_order, stop_on_failure=False):
        """populates the formats that will be supported"""
        stop_on_failure = True
        fmts = []
        for fmt in fmt_order:
            geom_results_funcs = 'get_%s_wildcard_geometry_results_functions' % fmt

            if fmt in self.format_class_map:
                cls = self.format_class_map[fmt](self)
                data = getattr(cls, geom_results_funcs)()
            elif hasattr(self, geom_results_funcs):
                data = getattr(self, geom_results_funcs)()
            else:
                msg = 'get_%s_wildcard_geometry_results_functions does not exist' % fmt
                if stop_on_failure:
                    raise RuntimeError(msg)
                self.log_error(msg)
            self._add_fmt(fmts, fmt, geom_results_funcs, data)

        if len(fmts) == 0:
            RuntimeError('No formats...expected=%s' % fmt_order)
        self.fmts = fmts
        #print("fmts =", fmts)

        self.supported_formats = [fmt[0] for fmt in fmts]
        print('supported_formats = %s' % self.supported_formats)
        #assert 'cart3d' in self.supported_formats, self.supported_formats
        if len(fmts) == 0:
            raise RuntimeError('no modules were loaded...')

    def _add_fmt(self, fmts, fmt, geom_results_funcs, data):
        """
        Adds a format

        Parameters
        ----------
        fmts : List[formats]
            format : List[fmt, macro_name, geo_fmt, geo_func, res_fmt, res_func]
            macro_name : ???
                ???
            geo_fmt : ???
                ???
            geo_func : ???
                ???
            res_fmt : ???
                ???
            res_func : ???
                ???
        fmt : str
            nastran, cart3d, etc.
        geom_results_funcs : str
            'get_nastran_wildcard_geometry_results_functions'
            'get_cart3d_wildcard_geometry_results_functions'
        data : function
            the outputs from ``get_nastran_wildcard_geometry_results_functions()``
            so 1 or more formats (macro_name, geo_fmt, geo_func, res_fmt, res_func)
        """
        msg = 'macro_name, geo_fmt, geo_func, res_fmt, res_func = data\n'
        msg += 'data = %s'
        if isinstance(data, tuple):
            assert len(data) == 5, msg % str(data)
            macro_name, geo_fmt, geo_func, res_fmt, res_func = data
            fmts.append((fmt, macro_name, geo_fmt, geo_func, res_fmt, res_func))
        elif isinstance(data, list):
            for datai in data:
                assert len(datai) == 5, msg % str(datai)
                macro_name, geo_fmt, geo_func, res_fmt, res_func = datai
                fmts.append((fmt, macro_name, geo_fmt, geo_func, res_fmt, res_func))
        else:
            raise TypeError(data)

    def _reset_model(self, name):
        """resets the grids; sets up alt_grids"""
        if hasattr(self, 'main_grids') and name not in self.main_grids:
            grid = vtk.vtkUnstructuredGrid()
            grid_mapper = vtk.vtkDataSetMapper()
            grid_mapper.SetInputData(grid)

            geom_actor = vtk.vtkLODActor()
            geom_actor.DragableOff()
            geom_actor.SetMapper(grid_mapper)
            self.rend.AddActor(geom_actor)

            self.grid = grid
            self.grid_mapper = grid_mapper
            self.geom_actor = geom_actor
            self.grid.Modified()

            # link the current "main" to the scalar bar
            scalar_range = self.grid_selected.GetScalarRange()
            self.grid_mapper.ScalarVisibilityOn()
            self.grid_mapper.SetScalarRange(scalar_range)
            self.grid_mapper.SetLookupTable(self.color_function)

            self.edge_actor = vtk.vtkLODActor()
            self.edge_actor.DragableOff()
            self.edge_mapper = vtk.vtkPolyDataMapper()

            # create the edges
            self.get_edges()
        else:
            self.grid.Reset()
            self.grid.Modified()

        # reset alt grids
        alt_names = self.alt_grids.keys()
        for alt_name in alt_names:
            self.alt_grids[alt_name].Reset()
            self.alt_grids[alt_name].Modified()

    #---------------------------------------------------------------------------
    def load_batch_inputs(self, inputs):
        geom_script = inputs['geomscript']
        if geom_script is not None:
            self.on_run_script(geom_script)

        if not inputs['format']:
            return
        form = inputs['format'].lower()
        input_filenames = inputs['input']
        results_filename = inputs['output']
        plot = True
        if results_filename:
            plot = False

        #print('input_filename =', input_filename)
        if input_filenames is not None:
            for input_filename in input_filenames:
                if not os.path.exists(input_filename):
                    msg = '%s does not exist\n%s' % (
                        input_filename, print_bad_path(input_filename))
                    self.log.error(msg)
                    if self.html_logging:
                        print(msg)
                    return
            for results_filenamei in results_filename:
                #print('results_filenamei =', results_filenamei)
                if results_filenamei is not None:
                    if not os.path.exists(results_filenamei):
                        msg = '%s does not exist\n%s' % (
                            results_filenamei, print_bad_path(results_filenamei))
                        self.log.error(msg)
                        if self.html_logging:
                            print(msg)
                        return

        #unused_is_geom_results = input_filename == results_filename and len(input_filenames) == 1
        unused_is_geom_results = False
        for i, input_filename in enumerate(input_filenames):
            if i == 0:
                name = 'main'
            else:
                name = input_filename
            #form = inputs['format'].lower()
            #if is_geom_results:
            #    is_failed = self.on_load_geometry_and_results(
            #        infile_name=input_filename, name=name, geometry_format=form,
            #        plot=plot, raise_error=True)
            #else:
            is_failed = self.on_load_geometry(
                infile_name=input_filename, name=name, geometry_format=form,
                plot=plot, raise_error=True)
        self.name = 'main'
        #print('keys =', self.nid_maps.keys())

        if is_failed:
            return
        if results_filename:  #  and not is_geom_results
            self.on_load_results(results_filename)

        post_script = inputs['postscript']
        if post_script is not None:
            self.on_run_script(post_script)
        self.on_reset_camera()
        self.vtk_interactor.Modified()

    #---------------------------------------------------------------------------
    def update_text_actors(self, subcase_id, subtitle, min_value, max_value, label):
        """
        Updates the text actors in the lower left

        Max:  1242.3
        Min:  0.
        Subcase: 1 Subtitle:
        Label: SUBCASE 1; Static
        """
        self.tool_actions.update_text_actors(subcase_id, subtitle, min_value, max_value, label)

    def create_text(self, position, label, text_size=18):
        """creates the lower left text actors"""
        self.tool_actions.create_text(position, label, text_size=text_size)

    def turn_text_off(self):
        """turns all the text actors off"""
        self.tool_actions.turn_text_off()

    def turn_text_on(self):
        """turns all the text actors on"""
        self.tool_actions.turn_text_on()

    def export_case_data(self, icases=None):
        """exports CSVs of the requested cases"""
        self.tool_actions.export_case_data(icases=icases)

    def on_load_user_geom(self, csv_filename=None, name=None, color=None):
        """
        Loads a User Geometry CSV File of the form:

        #    id  x    y    z
        GRID, 1, 0.2, 0.3, 0.3
        GRID, 2, 1.2, 0.3, 0.3
        GRID, 3, 2.2, 0.3, 0.3
        GRID, 4, 5.2, 0.3, 0.3
        grid, 5, 5.2, 1.3, 2.3  # case insensitive

        #    ID, nodes
        BAR,  1, 1, 2
        TRI,  2, 1, 2, 3
        # this is a comment

        QUAD, 3, 1, 5, 3, 4
        QUAD, 4, 1, 2, 3, 4  # this is after a blank line

        #RESULT,4,CENTROID,AREA(%f),PROPERTY_ID(%i)
        # in element id sorted order: value1, value2
        #1.0, 2.0 # bar
        #1.0, 2.0 # tri
        #1.0, 2.0 # quad
        #1.0, 2.0 # quad

        #RESULT,NODE,NODEX(%f),NODEY(%f),NODEZ(%f)
        # same difference

        #RESULT,VECTOR3,GEOM,DXYZ
        # 3xN

        Parameters
        ----------
        csv_filename : str (default=None -> load a dialog)
            the path to the user geometry CSV file
        name : str (default=None -> extract from fname)
            the name for the user points
        color : (float, float, float)
            RGB values as 0.0 <= rgb <= 1.0
        """
        self.tool_actions.on_load_user_geom(csv_filename=csv_filename, name=name, color=color)

    def on_load_csv_points(self, csv_filename=None, name=None, color=None):
        """
        Loads a User Points CSV File of the form:

        1.0, 2.0, 3.0
        1.5, 2.5, 3.5

        Parameters
        -----------
        csv_filename : str (default=None -> load a dialog)
            the path to the user points CSV file
        name : str (default=None -> extract from fname)
            the name for the user points
        color : (float, float, float)
            RGB values as 0.0 <= rgb <= 1.0
        """
        is_failed = self.tool_actions.on_load_csv_points(
            csv_filename=csv_filename, name=name, color=color)
        return is_failed

    #---------------------------------------------------------------------------
    def create_groups_by_visible_result(self, nlimit=50):
        """
        Creates group by the active result

        This should really only be called for integer results < 50-ish.
        """
        return self.group_actions.create_groups_by_visible_result(nlimit=nlimit)

    def create_groups_by_property_id(self):
        """
        Creates a group for each Property ID.

        As this is somewhat Nastran specific, create_groups_by_visible_result exists as well.
        """
        return self.group_actions.create_groups_by_property_id()

    #---------------------------------------------------------------------------
    def update_camera(self, code):
        self.view_actions.update_camera(code)

    def _update_camera(self, camera=None):
        self.view_actions._update_camera(camera)

    def on_pan_left(self, event):
        self.view_actions.on_pan_left(event)

    def on_pan_right(self, event):
        self.view_actions.on_pan_right(event)

    def on_pan_up(self, event):
        self.view_actions.on_pan_up(event)

    def on_pan_down(self, event):
        self.view_actions.on_pan_down(event)

    #------------------------------
    def rotate(self, rotate_deg, render=True):
        """rotates the camera by a specified amount"""
        self.view_actions.rotate(rotate_deg, render=render)

    def on_rotate_clockwise(self):
        """rotate clockwise"""
        self.view_actions.rotate(15.0)

    def on_rotate_cclockwise(self):
        """rotate counter clockwise"""
        self.view_actions.rotate(-15.0)

    #------------------------------
    def zoom(self, value):
        return self.view_actions.zoom(value)

    def on_increase_magnification(self):
        """zoom in"""
        self.view_actions.on_increase_magnification()

    def on_decrease_magnification(self):
        """zoom out"""
        self.view_actions.on_decrease_magnification()

    def set_focal_point(self, focal_point):
        """
        Parameters
        ----------
        focal_point : (3, ) float ndarray
            The focal point
            [ 188.25109863 -7. -32.07858658]
        """
        self.view_actions.set_focal_point(focal_point)

    def on_surface(self):
        """sets the main/toggle actors to surface"""
        self.view_actions.on_surface()

    def on_wireframe(self):
        """sets the main/toggle actors to wirefreme"""
        self.view_actions.on_wireframe()

    def on_take_screenshot(self, fname=None, magnify=None, show_msg=True):
        """
        Take a screenshot of a current view and save as a file

        Parameters
        ----------
        fname : str; default=None
            None : pop open a window
            str : bypass the popup window
        magnify : int; default=None
            None : use self.settings.magnify
            int : resolution increase factor
        show_msg : bool; default=True
            log the command
        """
        self.tool_actions.on_take_screenshot(fname=fname, magnify=magnify, show_msg=show_msg)

    def get_camera_data(self):
        """see ``set_camera_data`` for arguments"""
        return self.view_actions.get_camera_data()

    def on_set_camera(self, name, show_log=True):
        """see ``set_camera_data`` for arguments"""
        camera_data = self.cameras[name]
        self.on_set_camera_data(camera_data, show_log=show_log)

    def on_set_camera_data(self, camera_data, show_log=True):
        """
        Sets the current camera

        Parameters
        ----------
        camera_data : Dict[key] : value
            defines the camera
            position : (float, float, float)
                where am I is xyz space
            focal_point : (float, float, float)
                where am I looking
            view_angle : float
                field of view (angle); perspective only?
            view_up : (float, float, float)
                up on the screen vector
            clip_range : (float, float)
                start/end distance from camera where clipping starts
            parallel_scale : float
                ???
            parallel_projection : bool (0/1)
                flag?
                TODO: not used
            distance : float
                distance to the camera

        i_vector = focal_point - position
        j'_vector = view_up

        use:
           i x j' -> k
           k x i -> j
           or it's like k'
        """
        self.view_actions.on_set_camera_data(camera_data, show_log=show_log)

    @property
    def IS_GUI_TESTING(self):
        return 'test_' in sys.argv[0]
    @property
    def iren(self):
        return self.vtk_interactor
    @property
    def render_window(self):
        return self.vtk_interactor.GetRenderWindow()
