// nofocus.m: keeps an automated Godot test window from taking the keyboard focus or showing in the Dock.
// Loaded with DYLD_INSERT_LIBRARIES into the Godot 4.7.2 editor binary (its signature allows that) by tools/godot_bg/gdwin.
// Build: clang -dynamiclib -fobjc-arc -framework AppKit -arch arm64 -o nofocus.dylib nofocus.m
#import <AppKit/AppKit.h>
#import <objc/runtime.h>

static void sw(Class c, SEL s, IMP imp) {
    Method m = class_getInstanceMethod(c, s);
    if (m) method_setImplementation(m, imp);
}
static void app_activate_flag(id self, SEL _cmd, BOOL flag) {}
static void app_activate(id self, SEL _cmd) {}
static BOOL run_activate(id self, SEL _cmd, NSUInteger opts) { return NO; }
static BOOL run_activate_from(id self, SEL _cmd, id app, NSUInteger opts) { return NO; }
static BOOL (*orig_set_policy)(id, SEL, NSApplicationActivationPolicy);
static BOOL set_policy(id self, SEL _cmd, NSApplicationActivationPolicy p) {
    return orig_set_policy(self, _cmd, NSApplicationActivationPolicyAccessory);   // no Dock icon, never frontmost
}
static void win_show(id self, SEL _cmd, id sender) {
    NSWindow *w = (NSWindow *)self;
    w.collectionBehavior = NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorStationary | NSWindowCollectionBehaviorIgnoresCycle;
    if (getenv("GDWIN_FRONT")) [w orderFrontRegardless]; else [w orderBack:sender];
}
static void win_noop(id self, SEL _cmd) {}

__attribute__((constructor)) static void nofocus_init(void) {
    @autoreleasepool {
        sw([NSApplication class], @selector(activateIgnoringOtherApps:), (IMP)app_activate_flag);
        sw([NSApplication class], NSSelectorFromString(@"activate"), (IMP)app_activate);
        sw([NSRunningApplication class], @selector(activateWithOptions:), (IMP)run_activate);
        sw([NSRunningApplication class], NSSelectorFromString(@"activateFromApplication:options:"), (IMP)run_activate_from);
        Method m = class_getInstanceMethod([NSApplication class], @selector(setActivationPolicy:));
        if (m) {
            orig_set_policy = (BOOL (*)(id, SEL, NSApplicationActivationPolicy))method_getImplementation(m);
            method_setImplementation(m, (IMP)set_policy);
        }
        sw([NSWindow class], @selector(makeKeyAndOrderFront:), (IMP)win_show);
        sw([NSWindow class], @selector(makeKeyWindow), (IMP)win_noop);
        sw([NSWindow class], @selector(makeMainWindow), (IMP)win_noop);
        [[NSProcessInfo processInfo] beginActivityWithOptions:(NSActivityUserInitiated | NSActivityLatencyCritical) reason:@"automated test run"];
    }
}
