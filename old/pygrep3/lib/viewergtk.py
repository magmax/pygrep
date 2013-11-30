#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007, 2008, 2009, 2010  Miguel Ángel García Martínez \
# <miguelangel.garcia@gmail.com>"

#     This file is part of Pygrep.

#  Pygrep is free software; you can redistribute it and/or modify \
#it under the terms of the GNU General Public License as published by \
#the Free Software Foundation; either version 3 of the License, or \
#(at your option) any later version.

#  Pygrep is distributed in the hope that it will be useful, \
#but WITHOUT ANY WARRANTY; without even the implied warranty of \
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the \
#GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License along \
#with Pygrep (maybe in file "COPYING"); if not, write to the Free Software \
#Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

""" GTK viewer for Pygrep """

#Some parts of this file have been taken from MELD project. Thank you very much.

from pygrepinfo import PygrepInfo
import os
import time
import gtk
import gtk.glade
import gobject
import webbrowser
import signal
from viewergeneric import GenericViewer
from pygreplogger import PygrepLog
from paths import Paths
from EngineOptions import EnabledString, PersistentOptions, ExtendedOptions
from EnginePygrep import PygrepEngine
from EngineGeneric import EngineException, GenericEngine
import cgi
import sys
import utilities
from vieweroptions import ViewOptions

import gettext
for module in (gettext, gtk.glade):
    module.bindtextdomain ( 'pygrep', Paths().locale )
    module.textdomain ('pygrep')
_ = gettext.gettext

__author__ = "Miguel Ángel García Martínez <miguelangel.garcia@gmail.com>"
__date__  = "$28-dic-2009 19:49:45$"

def gtk_tree_view_add_text_column ( treeview, label, colnum, editable=False,
        colorized=False, sortby=-1 ):
    """
        Adds a Text Column to a treeview.
        label: The label of the column
        colnum: The possition of the model where the text has to be read.
        editable: If the column supports editing.
        colorized: If the text can have HTML marks to highlight something.
    """
    model = treeview.get_model()
    render = gtk.CellRendererText()
    render.props.editable = editable
    def change ( render, path, text ):
        """ allows to edit the column """
        model[path][colnum] = text
        return
    render.connect ( "edited", change )
    column = None
    if colorized:
        column = gtk.TreeViewColumn (label, render, markup=colnum)
    else:
        column = gtk.TreeViewColumn (label, render, text=colnum)
    column.set_sort_column_id ( sortby )
    treeview.append_column(column)
    return column

def gtk_tree_view_add_toggle_column ( treeview, label, colnum, editable=False ):
    """
        Adds a Boolean Column to a treeview, with a check box.
        label: The label of the column
        colnum: The possition of the model where the value has to be read.
        editable: If the column supports editing.
    """
    model = treeview.get_model()
    render = gtk.CellRendererToggle()
    render.set_property ( 'activatable', True )
    def toggle ( render, path ):
        """ Allows to edit the column """
        model[path][colnum] = not model[path][colnum]
        return
    if editable:
        render.connect ( "toggled", toggle )
    column = gtk.TreeViewColumn ( label, render, active=colnum)
    treeview.append_column (column)

def gtk_get_image ( imagename ):
    """
        Loads an image and returns a pixbuf.
        It will try different extensions.
    """
    logo = None
    for ext in [".svg", ".png"]:
        try:
            logo = gtk.gdk.pixbuf_new_from_file ( Paths.join ( Paths().glade,
                    imagename + ext ) )
            break
        except IOError:
            pass
        except Exception:
            pass
    PygrepLog().warning ( _("Image '%s' not found. ") % imagename )
    return logo

def gtk_fix_secondarybutton_error ( xml ):
    """
    There is a but in libglade with secondary buttons;
    This function is to correct this error.
    """
    hbutton = xml.get_widget ( "dialog-action_area" )
    helpbutton = xml.get_widget ( "button_help" )
    hbutton.set_child_secondary ( helpbutton, True )

def url_transformation ( text ):
    """
        Replaces a string for the HTML equivalent.
    """
    retval = None
    try:
        retval = cgi.escape ( unicode ( text, 'utf-8', 'replace' ) )
    except UnicodeDecodeError:
        PygrepLog().warning ('Error decoding text: "%s"', text )
        PygrepLog().debug ('Complete text: %s', [hex(ord(x)) for x in text])
        raise
    return retval
    
class PygrepGtk ( GenericViewer ):
    """
        Viewer for Pygrep using GTK.
    """
    COL_FIL_MATCH     = 0
    COL_FIL_FILENAME  = 1
    COL_FIL_PATH      = 2
    COL_FIL_PATHRAW   = 3
    COL_FIL_SIZE      = 4
    COL_FIL_TYPE      = 5
    COL_FIL_MODIFDATE = 6
    COL_FIL_MODIFSTR  = 7

    COL_MAT_MATCH     = 0
    COL_MAT_LINE      = 1
    COL_MAT_LINENO    = 2
    COL_MAT_FILENAME  = 3

    def main ( self ):
        """
            Main function for the viewer.
        """
        self.__show_beta_alert()

        self.model_files = None
        self.model_matches = None
        self.model_history = None
        self.treeviewfilter = None
        self.selected_filename = None
        self.selected_profile   = None

        gtk.gdk.threads_init()

        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
                "windowPygrep" )
        self.xml.signal_autoconnect(self)

        self.window = self.xml.get_widget("windowPygrep")

        self.__initialize_treeviews ()
        self.__initialize_toolbar   ()

        self.processed_files = 0
        self.options   = None
        self.engine    = None
        self.viewoptions = ViewOptions ()

        self.viewoptions.load_from_file ()

        self.initial_time = 0

        self.entry_empty = True
        self.__set_entry_text_color( True )

        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

        gtk.main()

    def __show_beta_alert ( self ):
        """ Shows the alert when a BETA version is been used. """
        if 'beta' in PygrepInfo.version.lower() \
                or 'alpha' in PygrepInfo.version.lower():
            msg = "%s\n%s\n%s\n%s\n%s" % \
                (
                _("Sorry. This is a BETA version."),
                _("It may not work well and may corrupt your profiles,"),
                _("so you must search for a release version."),
                _("Click CANCEL to abort or OK to continue with no warranty."),
                _("Thank you.") ) 
            dialog = gtk.MessageDialog ( None, gtk.DIALOG_MODAL,
                gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, msg)
            if dialog.run() == gtk.RESPONSE_CANCEL:
                sys.exit (0)

            dialog.hide()
            del (dialog)

    def __filter_entries ( self, model, itr, data=None):
        """ Choose if an line must be shown, depending on the selected file """
        value = model.get_value ( itr, self.COL_MAT_FILENAME )
        return value == self.selected_filename

    def __initialize_treeviews ( self ):
        """ Initializes the treeviews models and columns """
        self.model_files = \
            gtk.ListStore ( int, str, str, str, int, str, int, str )
        treeview = self.xml.get_widget ( "treeview_matched_files" )
        treeview.set_model ( self.model_files )
        gtk_tree_view_add_text_column ( treeview, _('#Matches'),
            self.COL_FIL_MATCH, sortby=self.COL_FIL_MATCH )
        gtk_tree_view_add_text_column ( treeview, _('Filename'),
            self.COL_FIL_FILENAME, sortby=self.COL_FIL_FILENAME )
        gtk_tree_view_add_text_column ( treeview, _('Full Filename Path'),
            self.COL_FIL_PATH, colorized=True, sortby=self.COL_FIL_PATH)
        gtk_tree_view_add_text_column ( treeview, _('Size'),
            self.COL_FIL_SIZE, sortby=self.COL_FIL_SIZE )
        gtk_tree_view_add_text_column ( treeview, _('Type'),
            self.COL_FIL_TYPE, sortby=self.COL_FIL_TYPE )
        gtk_tree_view_add_text_column ( treeview, _('Last modification'),
            self.COL_FIL_MODIFSTR, sortby=self.COL_FIL_MODIFDATE )
        treeview.get_selection ().connect ( "changed",
            self.on_treeview_matched_files_selection_changed )


        self.model_matches = gtk.ListStore ( int, str, int, str )
        treeview = self.xml.get_widget ( "treeview_matches_list" )

        self.treeviewfilter = self.model_matches.filter_new()
        self.treeviewfilter.set_visible_func ( self.__filter_entries )

        treeview.set_model ( self.treeviewfilter )

        gtk_tree_view_add_text_column ( treeview, _('Line'),
            self.COL_MAT_MATCH )
        gtk_tree_view_add_text_column ( treeview, _('Text'), self.COL_MAT_LINE,
            colorized=True )

        #history model
        self.model_history = gtk.ListStore ( bool, str )
        entry = self.xml.get_widget( "entry_search_exp" )
        completion = gtk.EntryCompletion ()
        completion.set_model ( self.model_history )
        completion.set_text_column ( 1 )
        entry.set_completion ( completion)

        
    def __initialize_toolbar ( self ):
        """ Initializes the toolbar """
        cbp = self.xml.get_widget("comboboxProfiles")
        model = gtk.ListStore ( str )
        cbp.set_model ( model )
        cell = gtk.CellRendererText()
        cbp.pack_start(cell, True)
        cbp.add_attribute(cell, 'text', 0)

        self.__reset_profiles()

        cbp.set_active ( 0 )
        
    def __reset_profiles ( self ):
        """ Reload profiles for the combobox. """
        cbp = self.xml.get_widget("comboboxProfiles")
        cbp.get_model ().clear ()
        cbp.append_text ( _("<Do not use>") )
        for profile in PersistentOptions().get_profile_list():
            cbp.append_text ( profile )
        cbp.set_active ( 0 )

    def __notify ( self, msg ):
        """ Shows a message in the status bar """
        statbar = self.xml.get_widget ( "statusbar" )
        statbar.push ( 0, msg )

    def destroy ( self ):
        """ Destroys the main window """
        if self.engine:
            self.engine.end = True
        gtk.main_quit ()

    def __set_entry_text_color ( self, empty ):
        entry = self.xml.get_widget ( "entry_search_exp" )
        buttons = ["button_refine", "button_search"]
        if empty:
            entry.set_text( _('<< You must enter here your search pattern >>') )
            entry.modify_text ( gtk.STATE_NORMAL, gtk.gdk.Color('#666666'))
            entry.modify_base ( gtk.STATE_NORMAL, gtk.gdk.Color('#ffffaa'))
        else:
            entry.modify_text ( gtk.STATE_NORMAL, gtk.gdk.Color('#000000'))
            entry.modify_base ( gtk.STATE_NORMAL, gtk.gdk.Color('#ffffff'))
        for buttonname in buttons:
            self.xml.get_widget ( buttonname ).set_sensitive ( not empty )

    def __search ( self ):
        """ Action of search """
        def update_progress ( entry, engine ):
            """ Handler for the time event to update the progress. """
            if not engine.end:
                entry.progress_pulse ()
            return not engine.end

        options = None
        if self.entry_empty:
            return
        if self.engine:
            self.engine.end = True
        self.engine = PygrepEngine ()
        if self.options:
            options = self.options
        else:
            options = ExtendedOptions ()
            dialog = EditProfileDialog ( self.window, options )
            if dialog.get_status() != EditProfileDialog.STATUS_OK:
                return

        options.regexp = \
            self.xml.get_widget ( 'toolbutton_regexp').get_active ()
        options.ignore_case = \
            self.xml.get_widget ( 'toolbutton_ignorecase').get_active ()

        self.engine.event_attach ( self.__file_match_action,
            GenericEngine.TOPIC_FILE )
        self.engine.event_attach ( self.__line_match_action,
            GenericEngine.TOPIC_LINE )
        self.engine.event_attach ( self.__end_search_action,
            GenericEngine.TOPIC_END )
        _entry = self.xml.get_widget ( "entry_search_exp" )
        options.pattern = _entry.get_text ()
        _entry.set_progress_fraction ( 0 )
        _entry.set_progress_pulse_step ( 0.1 )
        gobject.timeout_add ( 50, update_progress, _entry, self.engine )

        self.model_files.clear()
        self.model_matches.clear()

        #append it to the history
        self.__add_to_history ( options.pattern )

        self.selected_filename = None
        self.engine.options = options
        self.__notify ( _( 'Searching...' ) )
        self.engine.start ( )
        
    def __search_files ( self, filelist ):
        """ Action of search """
        def update_progress ( entry, engine ):
            entry.progress_pulse ()
            return not engine.end

        options = None
        if self.entry_empty:
            return
        if self.engine:
            self.engine.end = True
        self.engine = PygrepEngine ()
        if self.options:
            options = self.options
        else:
            options = ExtendedOptions ()
            dialog = EditProfileDialog ( self.window, options )
            if dialog.get_status() != EditProfileDialog.STATUS_OK:
                return

        options.regexp = \
            self.xml.get_widget ( 'toolbutton_regexp').get_active ()
        options.ignore_case = \
            self.xml.get_widget ( 'toolbutton_ignorecase').get_active ()

        self.engine.event_attach ( self.__file_match_action,
            GenericEngine.TOPIC_FILE )
        self.engine.event_attach ( self.__line_match_action,
            GenericEngine.TOPIC_LINE )
        self.engine.event_attach ( self.__end_search_action,
            GenericEngine.TOPIC_END )
        _entry = self.xml.get_widget ( "entry_search_exp" )
        options.pattern = _entry.get_text ()
        _entry.set_progress_fraction ( 0 )
        _entry.set_progress_pulse_step ( 0.1 )
        gobject.timeout_add ( 50, update_progress, _entry, self.engine )

        self.model_files.clear()
        self.model_matches.clear()

        #append it to the history
        self.__add_to_history ( options.pattern )

        self.selected_filename = None
        self.engine.options = options
        self.__notify ( _( 'Searching...' ) )
        for _file in filelist:
            self.engine.process_file ( options.pattern, None, _file )
        self.__end_search_action ( None )


    def __add_to_history ( self, pattern ):
        """ Adds a pattern to the history """
        for i in self.model_history:
            if i[1] == pattern:
                return
        self.model_history.append ( [ False, pattern ] )

    def __open_editor ( self, filename, linenumber=1 ):
        """ Launches the command to open the editor. """
        options = self.options
        if not options:
            options = ExtendedOptions ()
        _sp_comm = options.command.split()
        #expand variables in command
        for i in xrange ( len ( _sp_comm ) ):
            if "%F" in _sp_comm[i]:
                _sp_comm[i] = _sp_comm[i].replace("%F",
                    os.path.basename(filename))
            if "%P" in _sp_comm[i]:
                _sp_comm[i] = _sp_comm[i].replace("%P",
                    os.path.dirname(filename))
            if "%f" in _sp_comm[i]:
                _sp_comm[i] = _sp_comm[i].replace("%f", filename)
            if "%l" in _sp_comm[i]:
                _sp_comm[i] = _sp_comm[i].replace("%l", str(linenumber) )

        os.spawnvp ( os.P_NOWAIT, _sp_comm[0], _sp_comm )
        if options.min_launch:
            self.window.iconify ()

    # pylint: disable-msg=W0613
    def on_window1_destroy ( self, widget ):
        """ Action to launch when destroy window is requested """
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_imagemenuitemAbout_activate ( self, widget ):
        """ Action to launch when About button is pressed """
        AboutDialog ()

    # pylint: disable-msg=W0613
    def on_toolbuttonPreferences_clicked ( self, widget ):
        """ Action to launch when profile button is pressed """
        PreferencesDialog ( self.viewoptions, self.window )
        self.__reset_profiles()

    # pylint: disable-msg=W0613
    def on_toolbuttonHistory_clicked ( self, widget ):
        """ Action to launch when the button "history" is pressed """
        dialog = HistoryDialog ( self.model_history, self.window )
        if dialog.selected:
            entry = self.xml.get_widget ( "entry_search_exp" )
            entry.set_text ( dialog.selected )
            self.__search ()

        # pylint: disable-msg=W0613
    def on_toolbuttonEditProfile_clicked ( self, widget ):
        """ Action to launch when the button "edit profile" is pressed """
        EditProfileDialog ( self.window, self.options )

    # pylint: disable-msg=W0613
    def on_combobox_profiles_changed ( self, widget ):
        """ Action to launch when the selected profile changes """
        if self.options:
            self.options.save_to_file ( self.selected_profile )
        else:
            self.options = ExtendedOptions ()

        if widget.get_active () == 0:
            self.selected_profile = None
            self.options = None
        else:
            self.selected_profile = widget.get_active_text()
            self.options.load_from_file ( self.selected_profile )

        # pylint: disable-msg=W0613
    def on_imagemenuitemExit_activate ( self, widget ):
        """ Action to launch when exit button is pressed """
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_menuitemToolbarIconsText_toggled ( self, widget ):
        """ Action to launch when toolbar is set to Icons and Text. """
        toolbar = self.xml.get_widget ( "toolbar" )
        toolbar.set_property ( 'visible', True )
        toolbar.set_style ( gtk.TOOLBAR_BOTH )

    # pylint: disable-msg=W0613
    def on_menuitemToolbarIcons_toggled ( self, widget ):
        """ Action to launch when toolbar is set to Icons. """
        toolbar = self.xml.get_widget ( "toolbar" )
        toolbar.set_property ( 'visible', True )
        toolbar.set_style ( gtk.TOOLBAR_ICONS )

    # pylint: disable-msg=W0613
    def on_menuitemToolbarText_toggled ( self, widget ):
        """ Action to launch when toolbar is set to text. """
        toolbar = self.xml.get_widget ( "toolbar" )
        toolbar.set_property ( 'visible', True )
        toolbar.set_style ( gtk.TOOLBAR_TEXT )

    # pylint: disable-msg=W0613
    def on_menuitemToolbarInvisible_toggled ( self, widget ):
        """ Action to launch when toolbar is set to invisible. """
        toolbar = self.xml.get_widget ( "toolbar" )
        toolbar.set_property ( 'visible', False )

    # pylint: disable-msg=W0613
    def on_entry_search_exp_focus_in_event ( self, entry, button ):
        """ Action to launch when search entry gets focus """
        if self.entry_empty:
            entry.set_text('')
                   
        self.__set_entry_text_color( False)

    # pylint: disable-msg=W0613
    def on_entry_search_exp_focus_out_event ( self, entry, button ):
        """ Action to launch when search entry loses focus """
        self.entry_empty = not entry.get_text()
        
        self.__set_entry_text_color ( self.entry_empty )

    # pylint: disable-msg=W0613
    def on_toolbutton_help_clicked ( self, entry ):
        """ Action to launch when help button is clicked """
        PygrepHelp.open( PygrepHelp.MAIN_WINDOW )

    def __file_match_action ( self, event ):
        """ Action when a new matching file has been found """
        def addfile ( event ):
            """ Adds a file to matching files """
            path = ""
            pathraw = ""
            pango = self.viewoptions.format_fil_match.get_pango_string ()
            for token in event.path.tokenlist:
                if token.matchs:
                    path += pango % url_transformation ( token.token )
                else:
                    path += token.token
                pathraw += token.token
            fsize  = os.path.getsize ( pathraw )
            fmodif = os.path.getmtime ( pathraw )
            ftype  = utilities.get_file_type ( pathraw )
            self.model_files.append ( [event.matches, event.filename, path,
                pathraw, fsize, ftype, fmodif, time.ctime(fmodif) ] )

        gobject.idle_add ( addfile, event)

    def __line_match_action ( self, event ):
        """ Action when a new matching line has been found """
        def addline ( event ):
            """ Adds a line to matching lines """
            retval = ""
            linenum = -1
            pangolin = self.viewoptions.format_lin_match.get_pango_string ()
            pangopat = self.viewoptions.format_lin_match_exp.get_pango_string ()
            try:
                for line in event.linelist:
                    linetxt = ""
                    for token in line.tokenlist:
                        if token.matchs:
                            linetxt += pangopat \
                                % url_transformation( token.token)
                        else:
                            linetxt += url_transformation( token.token )
                    if line.matchs:
                        retval +=  pangolin % linetxt
                        if linenum == -1:
                            linenum = line.linenum
                    else:
                        retval += linetxt
                    retval += '\n'
                self.model_matches.append ( [ linenum, retval[:-1], linenum,
                    url_transformation ( event.filename ) ] )
            except UnicodeEncodeError:
                retval = _('<b>BINARY LINE</b>.')
            except UnicodeDecodeError:
                retval = _('<b>BINARY LINE</b>.')
            except Exception:
                retval = _('<b>BINARY LINE</b>.')
        gobject.idle_add ( addline, event )

    def __end_search_action ( self, event ):
        """ Action to launch when search ends. """
        def notify ( event ):
            if  event:
                msg = _('%s processed files in %s seconds') % \
                    ( event.processed_files, event.time_wasted )
            else:
                msg = _('Refined ended.')
            self.__notify ( msg )
            _entry = self.xml.get_widget ( "entry_search_exp" )
            _entry.set_progress_fraction ( 0 )
            _entry.set_progress_pulse_step ( 0 )

        gobject.idle_add ( notify, event )

    # pylint: disable-msg=W0613
    def on_button_search_clicked ( self, widget ):
        """ Action to launch when search button is clicked """
        if self.engine:
            self.engine.end = True
            self.engine = None
        self.__search()

    # pylint: disable-msg=W0613
    def on_button_search_again_clicked ( self, widget ):
        """ Action to launch when "Search Again" button is clicked """
        if self.engine:
            self.engine.end = True
            self.engine = None
        _filenames = []
        for row in self.model_files:
            _filenames.append ( row[self.COL_FIL_PATHRAW] )
        self.model_files.clear ()
        self.__search_files ( _filenames )

    # pylint: disable-msg=W0613
    def on_treeview_matched_files_selection_changed ( self, selection ):
        """ Action to launch when changes the file selected """
        if selection.count_selected_rows() == 0:
            return
        model, itr = selection.get_selected()
        self.selected_filename = model [itr] [self.COL_FIL_PATHRAW  ]
        self.treeviewfilter.refilter ()

    # pylint: disable-msg=W0613
    def on_toolbutton_regexp_toggled ( self, widget ):
        """ Action when regexp icon press """
        entry = self.xml.get_widget ( "entry_search_exp" )
        entry.set_icon_sensitive ( gtk.ENTRY_ICON_PRIMARY, widget.get_active() )

    # pylint: disable-msg=W0613
    def on_entry_search_exp_icon_press ( self, widget, pos, event ):
        """ Action when clean button is pressed. """
        entry = self.xml.get_widget ( "entry_search_exp" )
        if pos == gtk.ENTRY_ICON_SECONDARY:
            entry.set_text ('')
            self.entry_empty = True
            self.__set_entry_text_color( True )
            entry.grab_focus()
        elif pos == gtk.ENTRY_ICON_PRIMARY:
            dialog = RegExpDialog ( self.window )
            if dialog.regexp:
                entry.set_text ( dialog.regexp )
                self.entry_empty = False
                self.__search ()

    # pylint: disable-msg=W0613
    def on_entry_search_exp_activate ( self, widget ):
        """ Action when entry "Search" is activated """
        self.entry_empty = widget.get_text == ''
        self.__search ()

    # pylint: disable-msg=W0613
    def on_entry_search_exp_button_press_event ( self, widget, button ):
        """ Action when user clicks on entry "Search" """
        if self.engine:
            self.engine.end = True
            self.engine = None

    # pylint: disable-msg=W0613
    def on_menuitem_regexp_edit_activate ( self, widget ):
        """ Action when menu "reg exp edit" is pressed """
        dialog = RegExpDialog ( self.window )
        if dialog.regexp:
            entry = self.xml.get_widget ( "entry_search_exp" )
            entry.set_text ( dialog.regexp )
            #self.entry_empty = False
            self.__search ()

    # pylint: disable-msg=W0613
    def on_menuitem_history_activate ( self, widget ):
        """ Action when menu "history" is pressed """
        self.on_toolbuttonHistory_clicked ( None )

    def on_menuitem_preferences_activate ( self, widget ):
        """ Action when menu "Preferences" is pressed """
        self.on_toolbuttonPreferences_clicked ( None )

    # pylint: disable-msg=W0613
    def on_treeview_matched_files_row_activated ( self, treeview, path,
                column ):
        """ Action when treeview of files activates a row """
        model, itr = treeview.get_selection().get_selected()
        self.__open_editor ( model.get_value ( itr, self.COL_FIL_PATHRAW ) )

    # pylint: disable-msg=W0613
    def on_treeview_matches_list_row_activated ( self, treeview, path, column ):
        """ Action when treeview of lines activates a row """
        model, itr = treeview.get_selection().get_selected()
        self.__open_editor ( model.get_value ( itr, self.COL_MAT_FILENAME ),
                             model.get_value ( itr, self.COL_MAT_LINENO ) )

   

class PreferencesDialog:
    """ Manages the profiles dialog. """
    def __init__ ( self, viewoptions, parent=None ):
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialog_preferences')
        self.xml.signal_autoconnect ( self )

        self.dialog = self.xml.get_widget ( "dialog_preferences" )
        self.dialog.set_transient_for(parent)

        self.treeview = self.xml.get_widget ( "treeview_profiles" )
        self.treeview.get_selection().connect ( "changed",
            self.on_treeview_profiles_changed )

        self.__initialize_profiles_model ()
        self.__reload_profiles ()

        self.viewoptions = viewoptions

        gtk_fix_secondarybutton_error ( self.xml )

        self.dialog.run ()

    def __initialize_profiles_model ( self ):
        """ Initializes the model and treeview """
        self.profilesmodel = gtk.ListStore ( gobject.TYPE_STRING )
        self.treeview.set_model ( self.profilesmodel )

        gtk_tree_view_add_text_column ( self.treeview, _('Profile Name'), 0,
            False )

    def __reload_profiles ( self ):
        """ Loads the profiles """
        self.profilesmodel.clear ()
        for profile in PersistentOptions().get_profile_list():
            self.profilesmodel.append ( [profile] )

    # pylint: disable-msg=W0613
    def destroy ( self, widget=None ):
        """ Destroys the element """
        self.dialog.hide ()
        del ( self.dialog )

    # pylint: disable-msg=W0613
    def on_button_apply_clicked (self, widget ):
        """ Action for apply button """
        self.viewoptions.save_to_file ()
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_button_help_clicked ( self, widget ):
        """ Action for help button """
        PygrepHelp.open ( PygrepHelp.PREFERENCES_WINDOW )

    # pylint: disable-msg=W0613
    def on_button_add_profile_clicked ( self, widget ):
        """ Action for add profile button """
        dialog = NewProfileDialog (self.dialog)
        if dialog.profilename:
            options = ExtendedOptions ()
            options.save_to_file ( dialog.profilename )
            
        self.__reload_profiles()

    # pylint: disable-msg=W0613
    def on_button_dup_profile_clicked ( self, widget ):
        """ Action for duply profile button """
        dialog = NewProfileDialog (self.dialog)
        if dialog.profilename:
            model, itr = self.treeview.get_selection().get_selected()
            options = ExtendedOptions()
            options.load_from_file ( model[itr][0] )
            options.save_to_file ( dialog.profilename )
            
        self.__reload_profiles()

    # pylint: disable-msg=W0613
    def on_button_edit_profile_clicked ( self, widget ):
        """ Action for edit profile button """
        model, itr = self.treeview.get_selection().get_selected()
        options = ExtendedOptions ( )
        options.load_from_file ( model[itr][0] )
        EditProfileDialog ( self.dialog, options )

    # pylint: disable-msg=W0613
    def on_button_del_profile_clicked ( self, widget ):
        """ Action for delete profile button """
        model, itr = self.treeview.get_selection().get_selected()

        msg = _("The profile %s will be deleted forever. Are you sure?") % \
            model[itr][0]

        dialog = gtk.MessageDialog(None,
                                    gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_INFO,
                                    gtk.BUTTONS_YES_NO,
                                    msg)
        response = dialog.run()

        if response == gtk.RESPONSE_YES:
            PersistentOptions().delete_profile ( model[itr][0] )

        dialog.hide()
        del ( dialog )
        self.__reload_profiles()

    # pylint: disable-msg=W0613
    def on_treeview_profiles_changed ( self, selection ):
        """ Action to launch when treeview selection changes """
        dupbutton  = self.xml.get_widget ( "button_dup_profile" )
        editbutton = self.xml.get_widget ( "button_edit_profile" )
        delbutton  = self.xml.get_widget ( "button_del_profile" )
        activate   = selection.count_selected_rows() != 0
        dupbutton.set_sensitive ( activate )
        editbutton.set_sensitive ( activate )
        delbutton.set_sensitive ( activate )

    # pylint: disable-msg=W0613
    def on_button_filename_clicked ( self, widget ):
        """ Action to launch when filename properties button is clicked """
        TextPropertiesDialog ( self.viewoptions.format_fil_match, 
            self.dialog )

    # pylint: disable-msg=W0613
    def on_button_line_clicked ( self, widget ):
        """ Action to launch when line properties button is clicked """
        TextPropertiesDialog ( self.viewoptions.format_lin_match,
            self.dialog )

    # pylint: disable-msg=W0613
    def on_button_pattern_clicked ( self, widget ):
        """ Action to launch when pattern properties button is clicked """
        TextPropertiesDialog ( self.viewoptions.format_lin_match_exp,
            self.dialog )
    
 
class TextPropertiesDialog:
    """ Manages the dialog to choose text properties. """
    RET_OK     = 0
    RET_CANCEL = 1
    def __init__ ( self, textproperties, parent=None ):
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialog_text_properties')
        self.xml.signal_autoconnect ( self )

        self.dialog = self.xml.get_widget ( "dialog_text_properties" )
        self.dialog.set_transient_for(parent)

        #variables
        self._textProp       = textproperties.clone()
        self._textPropOrig   = textproperties
        self.var_foreground = None
        self.var_background = None
        self.return_status  = TextPropertiesDialog.RET_CANCEL
        
        self.text = self.xml.get_widget ( "label_example" ).get_text ()

        self.__initialize()


        gtk_fix_secondarybutton_error ( self.xml )

        self.dialog.run ()

    def __initialize ( self ):
        """ Initializes the values """
        def set_active_combo ( combo, value, default ):
            """ sets the text in a combo """
            combo.set_active ( 0 )
            model = combo.get_model()
            itr = combo.get_active_iter ()
            while ( itr ):
                if model[itr][0] == value:
                    combo.set_active_iter ( itr )
                    return
                itr = model.iter_next ( itr )
            combo.set_active_iter ( default )

        # To correct a libglade error, and put the help at left
        hbutton = self.xml.get_widget ( "dialog-action_area" )
        helpbutton = self.xml.get_widget ( "button_help" )
        hbutton.set_child_secondary ( helpbutton, True )

        # To correct a libglade error, set the combo elements.
        set_active_combo ( self.xml.get_widget ( "combobox_weight" ),
            self._textProp.weight, 2 )
        set_active_combo ( self.xml.get_widget ( "combobox_style" ),
            self._textProp.style, 0 )
        set_active_combo ( self.xml.get_widget ( "combobox_underline" ),
            self._textProp.underline, 0 )

        
    # pylint: disable-msg=W0613
    def destroy (self, widget=None):
        """ Destroys the History Dialog """
        self.dialog.hide ()
        del ( self.dialog )
        
    def _get_pattern ( self ):
        """ Returns the pattern """
        return self.xml.get_widget ("entry_pattern").get_text ()

    def _get_foreground ( self ):
        """ Returns the foreground """
        return self._textProp.foreground

    def _get_background ( self ):
        """ Returns the background """
        return self._textProp.background

    def _set_foreground ( self, value):
        """ Sets the foreground """
        self.var_foreground = value
        if self.xml.get_widget ( "checkbutton_foreground" ).get_active ():
            self._textProp.set_foreground ( value )
        else:
            self._textProp.set_foreground ( None )

    def _set_background ( self, value):
        """ Sets the background """
        self.var_background = value
        if self.xml.get_widget ( "checkbutton_background" ).get_active ():
            self._textProp.set_background ( value )
        else:
            self._textProp.set_background ( None )

    def _set_sample_text ( self ):
        pattern = self._get_pattern()
        markedpattern = self._textProp.get_pango_string() % pattern
        text = self.text.replace ( pattern, markedpattern )
        label = self.xml.get_widget ("label_example")
        label.set_text ( text )
        label.set_use_markup ( True )

    # pylint: disable-msg=W0613
    def on_button_cancel_clicked ( self, widget=None ):
        """ Action to launch when cancel button is pressed """
        self.return_status  = TextPropertiesDialog.RET_CANCEL
        self.destroy()

    # pylint: disable-msg=W0613
    def on_button_accept_clicked ( self, widget=None):
        """ Action to launch when accept button is pressed """
        self.return_status  = TextPropertiesDialog.RET_OK
        self._textPropOrig.copy ( self._textProp )
        self.destroy()

    # pylint: disable-msg=W0613
    def on_button_help_clicked ( self, widget ):
        """ Open the help for this dialog """
        PygrepHelp.open( PygrepHelp.TEXTPROP_WINDOW )

    # pylint: disable-msg=W0613
    def on_combobox_weight_changed ( self, widget ):
        """ Action to execute when weight value has changed """
        self._textProp.weight     = widget.get_active_text ()
        self._set_sample_text ()

    # pylint: disable-msg=W0613
    def on_combobox_style_changed ( self, widget ):
        """ Action to execute when the style changes """
        self._textProp.style      = widget.get_active_text ()
        self._set_sample_text ()

    # pylint: disable-msg=W0613
    def on_combobox_underline_changed ( self, widget ):
        """ Action to execute when underline value has changed """
        self._textProp.underline  = widget.get_active_text ()
        self._set_sample_text()

    # pylint: disable-msg=W0613
    def on_checkbutton_foreground_toggled ( self, widget ):
        """ Action to execute when foreground button is toggled """
        if widget.get_active():
            self._textProp.foreground = self.var_foreground
        else:
            self._textProp.foreground = None

        for wdg in ["label_fg_example", "button_foreground"]:
            self.xml.get_widget (wdg).set_sensitive ( widget.get_active() )
        self._set_sample_text()

    # pylint: disable-msg=W0613
    def on_checkbutton_background_toggled ( self, widget ):
        """ Action to execute when background checkbutton is toggled """
        if widget.get_active():
            self._textProp.background = self.var_background
        else:
            self._textProp.background = None

        for wdg in ["label_bg_example", "button_background"]:
            self.xml.get_widget (wdg).set_sensitive ( widget.get_active() )
        self._set_sample_text()

    # pylint: disable-msg=W0613
    def on_entry_pattern_changed ( self, widget ):
        """ Action to execute when the pattern has changed """
        self._set_sample_text()

    # pylint: disable-msg=W0613
    def on_button_foreground_clicked ( self, widget ):
        """ Action to manage the foreground button """
        dialog = gtk.ColorSelectionDialog ( _("Foreground Color") )
        selection = dialog.get_color_selection()
        if self.var_foreground:
            selection.set_current_color ( self.var_foreground )
        if dialog.run () == gtk.RESPONSE_OK:
            self._set_foreground( selection.get_current_color() )
            label = self.xml.get_widget ("label_fg_example")
            text = '<span foreground="%s">%s</span>' % (self.var_foreground,
                _("Example of color") )
            label.set_text ( text )
            label.set_use_markup ( True )

        dialog.destroy ()
        self._set_sample_text()

    # pylint: disable-msg=W0613
    def on_button_background_clicked ( self, widget ):
        """ Action to manage the background button. """
        dialog = gtk.ColorSelectionDialog ( _("Background Color") )
        selection = dialog.get_color_selection()
        if self.var_background:
            selection.set_current_color ( self.var_background )
        if dialog.run () == gtk.RESPONSE_OK:
            self._set_background( selection.get_current_color() )
            label = self.xml.get_widget ("label_bg_example")
            text = '<span background="%s">%s</span>' % (self.var_background,
                _("Example of color") )
            label.set_text ( text )
            label.set_use_markup ( True )

        dialog.destroy ()
        self._set_sample_text()


class NewProfileDialog:
    """
    Window to ask for a new profile.
    """
    def __init__ ( self, parent=None ):
        """ Initializer for the New Profile Dialog"""
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialogNewProfile')
        self.xml.signal_autoconnect ( self )

        self.dialog = self.xml.get_widget ( "dialogNewProfile" )
        self.dialog.set_transient_for(parent)

        self.profilename = None
        self.options     = None

        #gtk_fix_secondarybutton_error ( self.xml )

        self.dialog.run ()

    # pylint: disable-msg=W0613
    def destroy (self, widget=None):
        """ Operstions to perform to destroy the element. """
        self.dialog.hide ()
        del ( self.dialog )

    def __accept ( self ):
        entry = self.xml.get_widget ( "entryProfilename" )
        self.profilename = entry.get_text()
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_entryProfilename_activate ( self, widget):
        self.__accept()

    # pylint: disable-msg=W0613
    def on_buttonCancel_clicked ( self, widget ):
        """ Action when cancel button is pressed """
        self.destroy()

    # pylint: disable-msg=W0613
    def on_buttonAdd_clicked ( self, widget ):
        """ Action when add button is pressed """
        self.__accept ()

    # pylint: disable-msg=W0613
    def on_entryProfilename_changed ( self, widget ):
        """ Action when profilename changes. """
        entry = self.xml.get_widget ( "entryProfilename" )
        button = self.xml.get_widget ( "buttonAdd" )
        button.set_sensitive ( entry.get_text () != "" )



class EditProfileDialog:
    """ Manages the Edit Profile Dialog """
    STATUS_CANCEL = 0
    STATUS_OK     = 1

    def __init__ ( self, parent=None, options=None ):
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialog_edit_profile')
        self.xml.signal_autoconnect ( self )

        self.dialog = self.xml.get_widget ( "dialog_edit_profile" )
        self.dialog.set_transient_for ( parent )
        self.status = EditProfileDialog.STATUS_CANCEL

        if options:
            assert ( type ( options ) == ExtendedOptions )
            self.options = options
        else:
            self.options = ExtendedOptions()

        # treeview for Directories
        self.model_directories = gtk.ListStore ( bool, str )
        self.treeview_directories = \
            self.xml.get_widget ( "treeview_directories" )
        self.treeview_directories.set_model ( self.model_directories )
        gtk_tree_view_add_toggle_column ( self.treeview_directories,
            _('Enabled'), 0, True)
        gtk_tree_view_add_text_column ( self.treeview_directories,
            _('Directory'), 1, False)
        self.treeview_directories.get_selection().connect ( "changed",
            self.on_selection_directories_changed)

        #treeview for Inclusions
        self.model_inclusions = gtk.ListStore ( bool, str )
        self.treeview_inclusions = self.xml.get_widget ( "treeview_inclusions" )
        self.treeview_inclusions.set_model ( self.model_inclusions )
        gtk_tree_view_add_toggle_column ( self.treeview_inclusions,
            _('Enabled'), 0, True)
        gtk_tree_view_add_text_column ( self.treeview_inclusions, _('Pattern'),
            1, False)
        self.treeview_inclusions.get_selection().connect ( "changed",
            self.on_selection_inclusions_changed)

        #treeview for Exclusions
        self.treeview_exclusions = gtk.ListStore ( bool, str )
        self.model_exclusions = self.xml.get_widget ( "treeview_exclusions" )
        self.model_exclusions.set_model ( self.treeview_exclusions )
        gtk_tree_view_add_toggle_column ( self.model_exclusions,
            _('Enabled'), 0, True)
        gtk_tree_view_add_text_column ( self.model_exclusions, _('Pattern'),
            1, False)
        self.model_exclusions.get_selection().connect ( "changed",
            self.on_selection_exclusions_changed)

        self.__initialize()

        # To correct an libglade error, and put the help at left
        hbutton = self.xml.get_widget ( "dialog-action_area" )
        helpbutton = self.xml.get_widget ( "button_help" )
        hbutton.set_child_secondary ( helpbutton, True )

        gtk_fix_secondarybutton_error ( self.xml )

        self.dialog.run ()

    def __initialize ( self ):
        """
        Sets the default values, taken from self.options.
        """
        obj = self.xml.get_widget ( "spinbuttonBefore" )
        obj.set_value ( float ( self.options.lines_before ) )
        obj = self.xml.get_widget ( "spinbuttonAfter" )
        obj.set_value ( float ( self.options.lines_after ) )

        obj = self.xml.get_widget ( "entryCommand" )
        obj.set_text ( self.options.command )

        obj = self.xml.get_widget ( "checkbuttonMinimize" )
        obj.set_active ( self.options.min_launch == 'True')

        obj = self.xml.get_widget ( "spinbuttonFilelimit" )
        obj.set_value ( float ( self.options.max_size ) )


        for directory in self.options.directory_list:
            self.model_directories.append ( [directory.enabled, directory.str] )

        for item in self.options.inclusion_list:
            self.model_inclusions.append ( [item.enabled, item.str])

        for item in self.options.exclusion_list:
            self.treeview_exclusions.append ( [item.enabled, item.str])

    # pylint: disable-msg=W0613
    def destroy (self, widget=None):
        """ Destroys the dialog """
        self.dialog.hide ()
        del ( self.dialog )

    def get_status ( self ):
        """ Getter for the status of the dialog """
        return self.status

    # pylint: disable-msg=W0613
    def on_buttonClose_clicked ( self, widget ):
        """ Action to launch when the button close has been pressed """
        self.destroy()
        self.status = EditProfileDialog.STATUS_CANCEL
        return None

    def __model2vector ( self, model ):
        """
        Transforms a model into a EnabledString vector.
        The model must have two columns: the status and the string.
        """
        retval = []
        for row in model:
            retval.append ( EnabledString ( row[1], row[0] ) )
        return retval

    # pylint: disable-msg=W0613
    def on_buttonOK_clicked ( self, widget ):
        """ Action to launch when the OK button has been pressed """
        self.options.lines_before = \
            self.xml.get_widget ( "spinbuttonBefore" ).get_value_as_int ()
        self.options.lines_after  = \
            self.xml.get_widget ( "spinbuttonAfter" ).get_value_as_int ()
        self.options.directory_list = \
            self.__model2vector ( self.model_directories )
        self.options.inclusion_list = \
            self.__model2vector ( self.model_inclusions )
        self.options.exclusion_list = \
            self.__model2vector ( self.treeview_exclusions )
        self.options.command  = \
            self.xml.get_widget ( "entryCommand" ).get_text ()
        self.options.minimizeOnLaunch  = \
            self.xml.get_widget ( "checkbuttonMinimize" ).get_active()
        self.options.maxSize  = \
            self.xml.get_widget ( "spinbuttonFilelimit" ).get_value_as_int()

        self.options.save_to_file ( self.options.loaded_profile )

        self.destroy ()

        self.status = EditProfileDialog.STATUS_OK

        return self.options

    # pylint: disable-msg=W0613
    def on_selection_directories_changed ( self, selection ):
        """ Action to launch when the selection of directories changes """
        editbutton = self.xml.get_widget ( "button_dir_edit" )
        delbutton = self.xml.get_widget ( "button_dir_del" )
        activate = selection.count_selected_rows() != 0
        editbutton.set_sensitive ( activate )
        delbutton.set_sensitive ( activate )

    # pylint: disable-msg=W0613
    def on_selection_inclusions_changed ( self, selection ):
        """ Action to launch when the selection of inxlusions changes """
        editbutton = self.xml.get_widget ( "button_inc_edit" )
        delbutton = self.xml.get_widget ( "button_inc_del" )
        activate = selection.count_selected_rows() != 0
        editbutton.set_sensitive ( activate )
        delbutton.set_sensitive ( activate )

    # pylint: disable-msg=W0613
    def on_selection_exclusions_changed ( self, selection ):
        """ Action to launch when the selection of exclusions changes """
        editbutton = self.xml.get_widget ( "button_exc_edit" )
        delbutton = self.xml.get_widget ( "button_exc_del" )
        activate = selection.count_selected_rows() != 0
        editbutton.set_sensitive ( activate )
        delbutton.set_sensitive ( activate )

    # pylint: disable-msg=W0613
    def on_button_dir_add_clicked ( self, widget ):
        """ Action to launch when add directory button is clicked """
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK,
                gtk.RESPONSE_OK)
        fcd = gtk.FileChooserDialog( _("Add directory"), self.dialog,
            gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, buttons )
        fcd.set_filename ('.')
        if fcd.run() == gtk.RESPONSE_OK:
            self.model_directories.append ( [True, fcd.get_filename()])
        fcd.hide()
        del ( fcd )

    # pylint: disable-msg=W0613
    def on_button_dir_edit_clicked ( self, widget ):
        """ Action to launch when edit directory button is clicked """
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK,
            gtk.RESPONSE_OK)
        fc = gtk.FileChooserDialog( _("Add directory"), self.dialog,
            gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, buttons )
        model, itr = self.treeview_directories.get_selection().get_selected()
        fc.set_filename ( model[itr][1] )
        if fc.run() == gtk.RESPONSE_OK:
            model[itr][1] = fc.get_filename()
        fc.hide()
        del ( fc )

    # pylint: disable-msg=W0613
    def on_button_dir_del_clicked ( self, widget) :
        """ Action to launch when del directory button is clicked """
        self.__on_button_del_clicked ( self.treeview_directories )

    def __on_button_addedit_clicked ( self, label, text, value, treeview ):
        buttons = ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK,
            gtk.RESPONSE_OK )
        dialog = gtk.Dialog(label, self.dialog, gtk.DIALOG_MODAL, buttons )
        entry  = gtk.Entry ()
        if value:
            entry.set_text ( value )
        vbox = dialog.vbox
        # pylint: disable-msg=E1101
        vbox.pack_start ( gtk.Label (text), True, True, 0 )
        # pylint: disable-msg=E1101
        vbox.pack_start ( entry, True, True, 1 )
        # pylint: disable-msg=E1101
        vbox.show_all ()
        model = treeview.get_model()
        if dialog.run() == gtk.RESPONSE_OK:
            if not value:
                model.append ( [True, entry.get_text()] )
            else:
                model, itr = treeview.get_selection().get_selected()
                model[itr][1] = entry.get_text ()
        dialog.hide()
        del ( dialog )

    def __on_button_del_clicked ( self, treeview ):
        """ Action to launch when del button is clicked """
        model, itr = treeview.get_selection().get_selected()
        model.remove ( itr )

    # pylint: disable-msg=W0613
    def on_button_inc_add_clicked ( self, widget ):
        """ Action to launch when add inclusion button is clicked """
        self.__on_button_addedit_clicked(_('Inclusions'),
            _('Set the Inclusion Pattern'), None, self.treeview_inclusions)

    # pylint: disable-msg=W0613
    def on_button_inc_edit_clicked ( self, widget ):
        """ Action to launch when edit inclusion button is clicked """
        model, itr = self.treeview_inclusions.get_selection().get_selected()
        self.__on_button_addedit_clicked(_('Inclusions'),
            _('Set the Inclusion Pattern'), model[itr][1],
            self.treeview_inclusions)

    # pylint: disable-msg=W0613
    def on_button_inc_del_clicked ( self, widget) :
        """ Action to launch when del inclusion button is clicked """
        self.__on_button_del_clicked ( self.treeview_inclusions )

    # pylint: disable-msg=W0613
    def on_button_exc_add_clicked ( self, widget ):
        """ Action to launch when add exclusion button is clicked """
        self.__on_button_addedit_clicked(_('Exclusions'),
            _('Set the Exclusion Pattern'), None, self.model_exclusions)

    # pylint: disable-msg=W0613
    def on_button_exc_edit_clicked ( self, widget ):
        """ Action to launch when edit exclusion button is clicked """
        model, itr = self.model_exclusions.get_selection().get_selected()
        self.__on_button_addedit_clicked(_('Exclusion'),
            _('Set the Exclusion Pattern'), model[itr][1],
            self.model_exclusions)

    # pylint: disable-msg=W0613
    def on_button_exc_del_clicked ( self, widget) :
        """ Action to launch when del exclusion button is clicked """
        self.__on_button_del_clicked ( self.model_exclusions )

    # pylint: disable-msg=W0613
    def on_button_help_clicked ( self, widget ):
        """ Open the help for this dialog """
        PygrepHelp.open( PygrepHelp.EDITPROFILE_WINDOW )

class HistoryDialog:
    """ Manages the history dialog. """
    def __init__ ( self, model, parent=None ):
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialog_history')
        self.xml.signal_autoconnect ( self )

        self.dialog = self.xml.get_widget ( "dialog_history" )
        self.dialog.set_transient_for(parent)

        treeview = self.xml.get_widget ( "treeview_history" )
        treeview.set_model ( model )
        gtk_tree_view_add_toggle_column ( treeview, _('Save'), 0, True)
        gtk_tree_view_add_text_column ( treeview, _('Pattern'), 1, False)

        treeview.get_selection().connect ( "changed",
            self.on_selection_changed )

        self.selected = None

        # To correct an libglade error, and put the help at left
        hbutton = self.xml.get_widget ( "dialog-action_area" )
        helpbutton = self.xml.get_widget ( "button_help" )
        hbutton.set_child_secondary ( helpbutton, True )

        gtk_fix_secondarybutton_error ( self.xml )

        self.dialog.run ()

    # pylint: disable-msg=W0613
    def destroy (self, widget=None):
        """ Destroys the History Dialog """
        self.dialog.hide ()
        del ( self.dialog )

    # pylint: disable-msg=W0613
    def on_button_close_clicked ( self, widget=None ):
        """ Action to launch when close button is pressed """
        self.destroy()

    # pylint: disable-msg=W0613
    def on_selection_changed ( self, selection ):
        searchbutton = self.xml.get_widget ( "button_search" )
        searchbutton.set_sensitive ( selection.count_selected_rows() > 0 )

    # pylint: disable-msg=W0613
    def on_button_search_clicked ( self, widget ):
        treeview = self.xml.get_widget ( "treeview_history" )
        selection = treeview.get_selection ()
        if selection == None:
            self.destroy ()
        model, itr = selection.get_selected ()
        self.selected = model[itr][1]
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_button_help_clicked ( self, widget ):
        """ Open the help for this dialog """
        PygrepHelp.open( PygrepHelp.HISTORY_WINDOW )

class RegExpDialog:
    """ Manages the Regular Expresions Editor dialog. """
    def __init__ ( self, parent=None ):
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialog_regular_expresions')
        self.xml.signal_autoconnect ( self )

        self.regexp = None

        self.dialog = self.xml.get_widget ( "dialog_regular_expresions" )
        self.dialog.set_transient_for ( parent )

        gtk_fix_secondarybutton_error ( self.xml )

        self.dialog.run ()

    # pylint: disable-msg=W0613
    def destroy ( self, widget=None ):
        """ Destroys the widget. """
        self.dialog.hide ()
        del ( self.dialog )

    def __process_example ( self ):
        """ Process the example to show how it looks like """
        def __drawlines ( lines ):
            """ Adds a line to the label """
            _linetxt = ''
            style = '<span foreground="red" underline="single"><b>%s</b></span>'

            for _line in lines:
                for _token in _line.tokenlist:
                    try:
                        _text = url_transformation ( _token.token )
                    except UnicodeDecodeError:
                        _text = ''
                    if _token.matchs:
                        _linetxt += style % _text
                    else:
                        _linetxt += _text
                _linetxt += '\n'
            if _linetxt != '':
                _linetxt [:-1]
            label.set_text ( _linetxt )
            label.set_use_markup ( True )

        entry    = self.xml.get_widget ( "entry_regexp" )
        textview = self.xml.get_widget ( "textview_example" )
        label    = self.xml.get_widget ( "label_text" )

        _pattern = entry.get_text ()
        _buffer = textview.get_buffer()
        _text = _buffer.get_text ( *_buffer.get_bounds () )

        if len ( _pattern ) == 0:
            label.set_text ( _text )
            return

        engine = PygrepEngine ()
        engine.options.regexp = True

        try:
            _lines = engine.process_buffer ( _pattern, _text )
            __drawlines ( _lines )
        except EngineException as exc:
            label.set_text ( '<i>%s</i>' % exc )
            label.set_use_markup ( True )

    # pylint: disable-msg=W0613
    def on_button_help_clicked ( self, widget ):
        """ Open the help for this dialog """
        PygrepHelp.open( PygrepHelp.REGEXPTESTER_WINDOW )

    # pylint: disable-msg=W0613
    def on_button_close_clicked ( self, widget ):
        """ Event launched when close button is clicked """
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_button_search_clicked ( self, widget ):
        """ Event launched when search button is clicked """
        entry       = self.xml.get_widget ( "entry_regexp" )
        self.regexp = entry.get_text ()
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_entry_regexp_changed ( self, widget ):
        """ Event launched when the regular expresion changes """
        self.__process_example()

    # pylint: disable-msg=W0613
    def on_textview_example_key_release_event ( self, widget, event ):
        """ Event launched when any key is pressed """
        self.__process_example()

    # pylint: disable-msg=W0613
    def on_textview_example_button_release_event ( self, widget, event ):
        """ Event launched when any button is pressed """
        self.__process_example()

    # pylint: disable-msg=W0613
    def on_entry_regexp_icon_press ( self, widget, possition, event ):
        """ Event launched when the text-entry icon is pressed """
        rad = RegExpAssistantDialog ( self.dialog )
        if rad.regexp:
            entry = self.xml.get_widget ( "entry_regexp" )
            entry.set_text ( rad.regexp )

class RegExpAssistantDialog:
    """ Manages the Regular Expresions Asistant dialog. """
    def __init__ ( self, parent=None ):
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialog_regexp_assistant')
        self.xml.signal_autoconnect ( self )

        self.regexp = None

        self.dialog = self.xml.get_widget ( "dialog_regexp_assistant" )
        self.dialog.set_transient_for ( parent )

        self.treeview_model = None
        self.__initialize_treeview ()

        self.xml.get_widget ( 'combobox_type').set_active ( 0 )
        self.xml.get_widget ( 'combobox_long' ).set_active ( 0 )

        self.pat_period = ''
        self.regexp = None

        gtk_fix_secondarybutton_error ( self.xml )
        
        self.dialog.run ()

    # pylint: disable-msg=W0613
    def destroy ( self, widget=None ):
        """ Destroy the dialog """
        self.dialog.hide ()
        del ( self.dialog )

    def __initialize_treeview ( self ):
        """ Initializes the Treeview columns """
        treeview = self.xml.get_widget ( "treeview_body" )
        gtk_tree_view_add_text_column ( treeview, _("Type of entry"), 0 )
        gtk_tree_view_add_text_column ( treeview, _("Entry"), 1 )
        gtk_tree_view_add_text_column ( treeview, _("Repetitions"), 2 )
        gtk_tree_view_add_text_column ( treeview, _("Length"), 3 )

        self.treeview_model = \
            gtk.ListStore ( str, str, str, str, int, str, int )

        treeview.set_model ( self.treeview_model )

        self.treeview_model.connect ( 'rows-reordered',
            self.on_something_happened )

        treeview.get_selection ().connect ( "changed",
            self.on_treeview_selection_changed )

    @staticmethod
    def update_line ( etype, entry, rep, long):
        if not entry:
            return ''
        pat = ['(%s)%s%s', '[%s]%s%s', '[^%s]%s%s'] [etype]
        longpat = ''
        if rep > 0 and long == 1:
            longpat = '?'
        return pat % (entry, rep, longpat)

    def __update_regexp ( self ):
        """ Update the final pattern string """
        regexp = ''
        if self.xml.get_widget ('checkbutton_ignorecase').get_active ():
            regexp += '(?i)'

        if self.xml.get_widget ('checkbutton_beginning').get_active ():
            regexp += '^'

        for row in self.treeview_model:
            regexp += RegExpAssistantDialog.update_line \
                ( row[4], row[1], row[5], row[6] )

        if self.xml.get_widget ('checkbutton_ending').get_active ():
            regexp += '$'

        self.xml.get_widget ( "label_result" ).set_text ( regexp )

    def __open_character_selector ( self ):
        """ Open the Character Selector Dialog """
        return CharacterSelectorDialog ( self.dialog ).character

    # pylint: disable-msg=W0613
    def on_button_close_clicked ( self, widget ):
        """ Close the dialog """
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_button_accept_clicked ( self, widget ):
        """ Closes the window, but stores the value """
        self.regexp = self.xml.get_widget ( "label_result" ).get_text()
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_entry_dat_icon_press ( self, widget, icon, event ):
        """ An icon on the entry has been pressed """
        entry = self.xml.get_widget ( "entry_dat" )
        text = self.__open_character_selector ( )
        if not len (text):
            return
        pos = entry.get_position()
        entry.insert_text ( text, pos )
        entry.set_position ( pos + len ( text ) )
        self.__update_regexp ()

    # pylint: disable-msg=W0613
    def on_button_period_clicked ( self, widget ):
        """ The button of period has been pressed """
        dialog = RegexpPerioricityDialog ( self.dialog )
        if dialog.exitstatus == RegexpPerioricityDialog.RET_STATUS_CANCEL:
            return
        widget.set_label ( dialog.text )
        self.pat_period = dialog.pattern
        self.__update_regexp ()

    # pylint: disable-msg=W0613
    def on_something_happened ( self, widget, param1=None, param2=None ):
        """
        Event for almost all buttons to register when something has changed
        and allow to update the pattern string.
        """
        self.__update_regexp ()

    # pylint: disable-msg=W0613
    def on_button_add_clicked ( self, widget ):
        """ Event on button add """
        type  = self.xml.get_widget ( 'combobox_type')
        entry = self.xml.get_widget ( 'entry_dat').get_text ()
        rep   = self.xml.get_widget ( 'button_period')
        long  = self.xml.get_widget ( 'combobox_long')
        values = []
        values.append ( type.get_active_text () )
        values.append ( entry )
        values.append ( rep.get_label() )
        values.append ( long.get_active_text () )
        values.append ( type.get_active () )
        values.append ( self.pat_period )
        values.append ( long.get_active () )

        self.treeview_model.append ( values )
        self.__update_regexp ()

    # pylint: disable-msg=W0613
    def on_button_del_clicked ( self, widget ):
        """ Event clicked on button for row removal """
        treeview = self.xml.get_widget ( "treeview_body" )
        model, itr = treeview.get_selection().get_selected()
        model.remove ( itr )
        self.__update_regexp ()

    # pylint: disable-msg=W0613
    def on_entry_dat_changed ( self, entry ):
        """ Event changed on data entry """
        if not entry.get_text ():
            selection = self.xml.get_widget ( "treeview_body" ).get_selection ()
            selection.unselect_all ()
            self.xml.get_widget ( 'button_add' ).set_sensitive ( False )
        else:
            self.xml.get_widget ( 'button_add' ).set_sensitive ( True )

    # pylint: disable-msg=W0613
    def on_treeview_selection_changed ( self, selection ):
        """ Event selection changed on treeview """
        active = selection.count_selected_rows ()
        self.xml.get_widget ( 'button_update' ).set_sensitive ( active )
        self.xml.get_widget ( 'button_del' ).set_sensitive ( active )

    # pylint: disable-msg=W0613
    def on_button_update_clicked ( self, widget ):
        """ Event clicked on button for row update """
        treeview = self.xml.get_widget ( "treeview_body" )
        model, itr = treeview.get_selection().get_selected ()
        type  = self.xml.get_widget ( 'combobox_type')
        entry = self.xml.get_widget ( 'entry_dat' ).get_text ()
        rep   = self.xml.get_widget ( 'button_period' )
        long  = self.xml.get_widget ( 'combobox_long' )
        model[itr][0] = type.get_active_text ()
        model[itr][1] = entry
        model[itr][2] = rep.get_label ()
        model[itr][3] = long.get_active_text ()
        model[itr][4] = type.get_active ()
        model[itr][5] = self.pat_period
        model[itr][6] = long.get_active ()

        self.__update_regexp ()

    # pylint: disable-msg=W0613
    def on_button_help_clicked ( self, widget ):
        """ Open the help for this dialog """
        PygrepHelp.open( PygrepHelp.REGEXPASSIS_WINDOW )

class CharacterSelectorDialog:
    """ Manages a dialog to select a kind of character """
    def __init__ ( self, parent=None ):
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialog_character_selector')
        self.xml.signal_autoconnect ( self )

        self.regexp = None

        self.dialog = self.xml.get_widget ( "dialog_character_selector" )
        self.dialog.set_transient_for ( parent )

        self.character = ''

        gtk_fix_secondarybutton_error ( self.xml )

        self.dialog.run ()

    # pylint: disable-msg=W0613
    def destroy ( self, widget=None ):
        """ Destroy the element """
        self.dialog.hide ()
        del ( self.dialog )

    # pylint: disable-msg=W0613
    def on_button_accept_clicked ( self, widget ):
        """ Event click on button accept """
        buttons = [
            'radiobutton_any',
            'radiobutton_alpha', 'radiobutton_nonalpha',
            'radiobutton_decimal', 'radiobutton_nondecimal',
            'radiobutton_white', 'radiobutton_nonwhite'
            ]
        values = {
            'radiobutton_any':'.',
            'radiobutton_alpha':'\w',
            'radiobutton_nonalpha':'\W',
            'radiobutton_decimal':'\d',
            'radiobutton_nondecimal':'\D',
            'radiobutton_white':'\s',
            'radiobutton_nonwhite':'\S'
        }
        retval = 0
        for button in buttons:
            if self.xml.get_widget ( button ).get_active():
                retval = values [button]
                break
        self.character = retval
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_button_close_clicked ( self, widget ):
        """ Event click on button close """
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_button_help_clicked ( self, widget ):
        """ Open the help for this dialog """
        PygrepHelp.open( PygrepHelp.REGEXPCHAR_WINDOW )

class RegexpPerioricityDialog:
    """ Manages a dialog to select the perioricity of an element """
    RET_STATUS_OK = 0
    RET_STATUS_CANCEL = 1
    def __init__ ( self, parent=None ):
        self.xml = gtk.glade.XML ( Paths.join ( Paths().glade, 'pygrep.glade' ),
            'dialog_regex_period')
        self.xml.signal_autoconnect ( self )

        self.regexp = None

        self.dialog = self.xml.get_widget ( "dialog_regex_period" )
        self.dialog.set_transient_for ( parent )

        self.pattern = ''
        self.text = ''
        self.exitstatus = RegexpPerioricityDialog.RET_STATUS_CANCEL

        gtk_fix_secondarybutton_error ( self.xml )

        self.dialog.run ()

    # pylint: disable-msg=W0613
    def destroy ( self, widget=None ):
        """ Destroy this object """
        self.dialog.hide ()
        del ( self.dialog )

    # pylint: disable-msg=W0613
    def on_button_accept_clicked ( self, widget ):
        """ Event clicked on button accept """
        retval = 0
        if self.xml.get_widget ( 'radiobutton_once' ).get_active():
            retval = ''
            self.text = _('only once')
        elif self.xml.get_widget ( 'radiobutton_maybe' ).get_active():
            retval = '?'
            self.text = _('maybe once')
        elif self.xml.get_widget ( 'radiobutton_zeroormore' ).get_active():
            retval = '*'
            self.text = _('zero or more times')
        elif self.xml.get_widget ( 'radiobutton_oneormore' ).get_active():
            retval = '+'
            self.text = _('one or more times')
        elif self.xml.get_widget ( 'radiobutton_exactly' ).get_active():
            spin = self.xml.get_widget ( 'spinbutton_times' )
            retval = '{%d}' % spin.get_value()
            self.text = _('exactly %d times') % spin.get_value()
        elif self.xml.get_widget ( 'radiobutton_between' ).get_active():
            spinfrom = self.xml.get_widget ( 'spinbutton_from' )
            spinto   = self.xml.get_widget ( 'spinbutton_to' )
            retval = '{%d,%d}' % ( spinfrom.get_value(), spinto.get_value() )
            self.text = _('between %d and %d times') % \
                ( spinfrom.get_value(), spinto.get_value() )

        self.pattern = retval
        self.exitstatus = RegexpPerioricityDialog.RET_STATUS_OK
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_button_cancel_clicked ( self, widget ):
        """ Event click on button cancel """
        self.exitstatus = RegexpPerioricityDialog.RET_STATUS_CANCEL
        self.destroy ()

    # pylint: disable-msg=W0613
    def on_spinbutton_times_value_changed ( self, widget, button=None ):
        """ Event change on spin for X times """
        self.xml.get_widget ( 'radiobutton_exactly' ).set_active( True )

    # pylint: disable-msg=W0613
    def on_spinbutton_from_value_changed ( self, widget, button=None ):
        """ Event change on spin for "from" times """
        self.xml.get_widget ( 'radiobutton_between' ).set_active( True )

    # pylint: disable-msg=W0613
    def on_spinbutton_to_value_changed ( self, widget, button=None ):
        """ Event change on spin for 'to' times """
        self.xml.get_widget ( 'radiobutton_between' ).set_active( True )

    # pylint: disable-msg=W0613
    def on_eventbox_between_button_press_event ( self, widget, button ):
        """ Event click near the checkbox of between """
        self.xml.get_widget ( 'radiobutton_between' ).set_active( True )

    # pylint: disable-msg=W0613
    def on_eventbox_exactly_button_press_event ( self, widget, button ):
        """ Event click near the checkbox of exactly N times """
        self.xml.get_widget ( 'radiobutton_exactly' ).set_active( True )

    # pylint: disable-msg=W0613
    def on_button_help_clicked ( self, widget ):
        """ Open the help for this dialog """
        PygrepHelp.open( PygrepHelp.REGEXPPERID_WINDOW )


class AboutDialog:
    """ Build and manage the About dialog. """
    def __init__(self):
        logo = gtk_get_image ( "logo" )

        about = gtk.AboutDialog()
        about.set_license ( PygrepInfo.license_text )
        about.set_copyright ( PygrepInfo.copyright_text )
        about.set_website ( PygrepInfo.url )
        about.set_name ( "Pygrep " + PygrepInfo.version )
        about.set_comments ( PygrepInfo.description )
        about.set_authors ( PygrepInfo.author_list )
        about.set_artists( PygrepInfo.artists )
        about.set_logo ( logo )
        about.set_icon ( logo )
        about.set_wrap_license ( True )

        about.connect ("response", lambda d, r: d.destroy())
        about.connect ("close", self.on_destroy)
        about.connect ("destroy", self.on_destroy)

        about.run()

    # pylint: disable-msg=R0201
    def on_destroy(self, about):
        """ Destroys the dialog. """
        about.hide()
        del (about)
        del (self)


class PygrepHelp ( object ):
    """ Class to call the browser for a help webpage.  """
    HOST                = 'http://www.magmax.org/drupal'
    MAIN_WINDOW         = '/pygrep3/main'
    EDITPROFILE_WINDOW  = ''
    HISTORY_WINDOW      = ''
    PREFERENCES_WINDOW  = '/pygrep3/preferences1'
    REGEXPASSIS_WINDOW  = '/pygrep3/regexpassistant'
    REGEXPCHAR_WINDOW   = '/pygrep3/regexpcharacter'
    REGEXPPERID_WINDOW  = '/pygrep3/regexpperioricity'
    REGEXPTESTER_WINDOW = '/pygrep3/regexptester'
    TEXTPROP_WINDOW     = '/pygrep3/textproperties'

    @staticmethod
    def opencommon ( ):
        """
        Open a common web page.
        """
        try:
            webbrowser.open_new_tab ( PygrepInfo.url )
        except IOError:
            pass
        except Exception:
            pass

    @staticmethod
    def open ( url ):
        """
        Open a predefined url. If it fails, tries to open the default page.
        """
        try:
            webbrowser.open_new_tab ( PygrepHelp.HOST + url )
        except IOError:
            PygrepHelp.opencommon ( )
        except Exception:
            PygrepHelp.opencommon ( )
             
