import wx
import wx.html


from . import GetParam

FormSubmitEventType = wx.NewEventType()

EVT_FORM_SUBMIT = wx.PyEventBinder(FormSubmitEventType)

class FormSubmitEvent(wx.PyEvent):
    """
        Event indication a form was submitted.
        form is the form object being submitted
        args is a dict of form arguments
    """
    def __init__(self, form, args):
        wx.PyEvent.__init__(self)
        self.SetEventType(FormSubmitEventType)
        self.form = form
        self.args = args
    
class HTMLForm(object):
    def __init__(self, tag, container):
        self.container = container
        self.fields = []
        self.action = GetParam(tag, "ACTION", default=None)
        self.method = GetParam(tag, "METHOD", "GET")
        if self.method not in ("GET", "POST"):
            self.method = "GET"
            
    def hitSubmitButton(self):
        from . import input
        for field in self.fields:
            if isinstance(field, input.SubmitButton):
                field.OnClick(None)
                return
                
    def submit(self, btn=None):
        args = self.createArguments()
        if btn and btn.name:
            args[btn.name] = btn.GetLabel()
        evt = FormSubmitEvent(self, args)
        self.container.ProcessEvent(evt)
        
    def createArguments(self):
        args = {}
        for field in self.fields:
            if field.name and field.IsEnabled():
                val = field.GetValue()
                if val is None:
                    continue
                args[field.name] = val
        return args



class FormTagHandler(wx.html.HtmlWinTagHandler):
    typeregister = {}
    
    @classmethod
    def registerType(klass, type, controlClass):
        klass.typeregister[type] = controlClass
    
    def __init__(self):
        self.form = None
        wx.html.HtmlWinTagHandler.__init__(self)
    
    def GetSupportedTags(self):
        return "FORM,INPUT,TEXTAREA,SELECT,OPTION"
        
    def HandleTag(self, tag):
        try:
            handler = getattr(self, "Handle"+tag.GetName().upper())
            return handler(tag)
        except:
            import traceback
            traceback.print_exc()
        
    def HandleFORM(self, tag):
        self.form = HTMLForm(tag, self.GetParser().GetWindowInterface().GetHTMLWindow())
        self.cell = self.GetParser().OpenContainer()
        self.ParseInner(tag)
        self.GetParser().CloseContainer()
        self.form = None
        self.optionList = []
        return True
    
    def HandleINPUT(self, tag):
        if tag.HasParam("type"):
            ttype = tag.GetParam("type").upper()
        else:
            ttype = "TEXT"
        klass = self.typeregister[ttype]
        self.createControl(klass, tag)
        return False
        
    def HandleTEXTAREA(self, tag):
        klass = self.typeregister["TEXTAREA"]
        self.createControl(klass, tag)
        #Don't actually call ParseInner, but lie and said we did.
        #This should skip us ahead to the next tag, and let us 
        #retrieve the text verbatem from the text area
        return True
    
    def HandleSELECT(self, tag):
        if tag.HasParam("MULTIPLE"):
            pass
        from .select import SingleSelectControl
        self.optionList = []
        #gather any/all nested options
        self.ParseInner(tag)
        parent = self.GetParser().GetWindowInterface().GetHTMLWindow()
        if 'wxMSW' in wx.PlatformInfo:
            #HAX: wxChoice has some bizarre SetSize semantics that
            #interact poorly with HtmlWidgetCell. Most notably, resizing the control
            #triggers a paint event (in the parent, I guess?) which in turn calls Layout()
            #which calls SetSize again and so on. An extra "layer" between the control
            #and the window keeps the recursion from happening.
            object = wx.Panel(parent)
            select = SingleSelectControl(object, self.form, tag, self.GetParser(), self.optionList)
            sz = wx.BoxSizer()
            sz.Add(select, 1, wx.EXPAND)
            object.SetSizer(sz)
            object.SetSize(select.GetSize())
        else:
            object = SingleSelectControl(parent, self.form, tag, self.GetParser(), self.optionList)
        cell = self.GetParser().GetContainer()
        
        
        cell.InsertCell(
            wx.html.HtmlWidgetCell(object)
        )
        self.optionList = []
        return True
        
    def HandleOPTION(self, tag):
        self.optionList.append(tag)
        return True
        
    def createControl(self, klass, tag):
        parent = self.GetParser().GetWindowInterface().GetHTMLWindow()
        object = klass(parent, self.form, tag, self.GetParser())
        if not isinstance(object, wx.Window):
            return
        cell = self.GetParser().GetContainer()
        cell.InsertCell(
            wx.html.HtmlWidgetCell(object)
        )
        
        
        
        
wx.html.HtmlWinParser_AddTagHandler(FormTagHandler)


