#!/usr/bin/env python3
"""Real Mach-O fixtures verify that Neo packaging cannot retain Intel helpers."""
from pathlib import Path
import importlib.util,subprocess,tempfile,unittest,shutil
ROOT=Path(__file__).resolve().parents[1]
class PackageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  spec=importlib.util.spec_from_file_location('package_neo',ROOT/'scripts/package-neo.py');cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def fixture(self):
  c=self.root/'hello.c';c.write_text('int main(void){return 0;}\n')
  for arch in ['arm64','x86_64']:subprocess.run(['xcrun','clang','-arch',arch,str(c),'-o',str(self.root/arch)],check=True)
  app=self.root/'Subler Neo.app';main=app/'Contents/MacOS/Neo';main.parent.mkdir(parents=True)
  subprocess.run(['lipo','-create',str(self.root/'arm64'),str(self.root/'x86_64'),'-output',str(main)],check=True)
  nested=app/'Contents/Frameworks/Updater.framework/Versions/A/Updater';nested.parent.mkdir(parents=True);shutil.copy2(main,nested)
  return app,main,nested
 def test_all_embedded_macho_are_thinned(self):
  app,main,nested=self.fixture();original=main.read_bytes();copy=self.root/'prepared.app';shutil.copytree(app,copy)
  entries=self.module.thin_bundle(copy)
  self.assertEqual(len(entries),2)
  for path in [copy/main.relative_to(app),copy/nested.relative_to(app)]:self.assertEqual(subprocess.check_output(['lipo','-archs',str(path)],text=True).split(),['arm64'])
  self.assertEqual(main.read_bytes(),original)
 def test_intel_only_helper_is_rejected(self):
  app,main,nested=self.fixture();shutil.copy2(self.root/'x86_64',nested)
  with self.assertRaisesRegex(RuntimeError,'arm64'):self.module.thin_bundle(app)
 def test_missing_non_system_dylib_is_rejected(self):
  app,main,nested=self.fixture()
  libsource=self.root/'missing.c';libsource.write_text('int missing(void){return 0;}\n')
  library=self.root/'libmissing.dylib'
  subprocess.run(['xcrun','clang','-arch','arm64','-dynamiclib',str(libsource),'-Wl,-install_name,@rpath/libmissing.dylib','-o',str(library)],check=True)
  source=self.root/'consumer.c';source.write_text('extern int missing(void);int main(void){return missing();}\n')
  subprocess.run(['xcrun','clang','-arch','arm64',str(source),str(library),'-o',str(main)],check=True)
  entries=self.module.thin_bundle(app)
  with self.assertRaisesRegex(RuntimeError,'libmissing.dylib'):self.module.validate_dependencies(app,entries)
 def test_non_executable_resources_untouched(self):
  app,main,nested=self.fixture();resource=app/'Contents/icon.png';resource.write_bytes(b'PNG resource fixture')
  self.module.thin_bundle(app);self.assertEqual(resource.read_bytes(),b'PNG resource fixture')
 def linked_fixture(self, location='Frameworks', runpath='@executable_path/../Frameworks', install_name='@rpath/libfixture.dylib'):
  app=self.root/'Subler Neo.app';main=app/'Contents/MacOS/Neo';main.parent.mkdir(parents=True,exist_ok=True)
  library=app/'Contents'/location/'libfixture.dylib';library.parent.mkdir(parents=True,exist_ok=True)
  source=self.root/'library.c';source.write_text('int fixture(void){return 0;}\n')
  subprocess.run(['xcrun','clang','-arch','arm64','-dynamiclib',str(source),'-Wl,-install_name,'+install_name,'-o',str(library)],check=True)
  source=self.root/'consumer.c';source.write_text('extern int fixture(void);int main(void){return fixture();}\n')
  flags=['-Wl,-rpath,'+runpath] if runpath else []
  subprocess.run(['xcrun','clang','-arch','arm64',str(source),str(library),*flags,'-o',str(main)],check=True)
  return app,main,library
 def test_library_present_but_outside_runpath_is_rejected(self):
  app,main,library=self.linked_fixture(location='Resources')
  with self.assertRaisesRegex(RuntimeError,'libfixture.dylib'):
   self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_valid_executable_runpath_and_loader_relative_reference(self):
  for name in ['@rpath/libfixture.dylib','@loader_path/../Frameworks/libfixture.dylib']:
   with self.subTest(install_name=name):
    app,main,library=self.linked_fixture(install_name=name)
    self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_transitive_library_inherits_executable_runpath(self):
  app,main,library=self.linked_fixture()
  parent=app/'Contents/Frameworks/libparent.dylib'
  source=self.root/'parent.c';source.write_text('extern int fixture(void);int parent(void){return fixture();}\n')
  subprocess.run(['xcrun','clang','-arch','arm64','-dynamiclib',str(source),str(library),'-Wl,-install_name,@rpath/libparent.dylib','-o',str(parent)],check=True)
  source=self.root/'parent-consumer.c';source.write_text('extern int parent(void);int main(void){return parent();}\n')
  subprocess.run(['xcrun','clang','-arch','arm64',str(source),str(parent),'-Wl,-rpath,@executable_path/../Frameworks','-o',str(main)],check=True)
  self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_loader_runpath_uses_declaring_library_directory(self):
  app,main,library=self.linked_fixture(location='Frameworks/Nested')
  parent=app/'Contents/Frameworks/libparent.dylib'
  source=self.root/'parent.c';source.write_text('extern int fixture(void);int parent(void){return fixture();}\n')
  subprocess.run(['xcrun','clang','-arch','arm64','-dynamiclib',str(source),str(library),'-Wl,-install_name,@rpath/libparent.dylib','-Wl,-rpath,@loader_path/Nested','-o',str(parent)],check=True)
  source=self.root/'parent-consumer.c';source.write_text('extern int parent(void);int main(void){return parent();}\n')
  subprocess.run(['xcrun','clang','-arch','arm64',str(source),str(parent),'-Wl,-rpath,@executable_path/../Frameworks','-o',str(main)],check=True)
  self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_nested_helper_cannot_borrow_main_executable_runpaths(self):
  app,main,library=self.linked_fixture()
  helper=app/'Contents/Helpers/Helper';helper.parent.mkdir()
  source=self.root/'consumer.c'
  subprocess.run(['xcrun','clang','-arch','arm64',str(source),str(library),'-o',str(helper)],check=True)
  with self.assertRaisesRegex(RuntimeError,'libfixture.dylib'):
   self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_library_symlink_outside_bundle_is_rejected(self):
  app,main,library=self.linked_fixture();outside=self.root/'outside.dylib';library.rename(outside);library.symlink_to(outside)
  with self.assertRaisesRegex(RuntimeError,'libfixture.dylib'):
   self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_escaped_first_runpath_cannot_be_hidden_by_later_bundled_copy(self):
  app,main,library=self.linked_fixture();outside=self.root/'outside.dylib';shutil.copy2(library,outside)
  fallback=app/'Contents/Resources/libfixture.dylib';fallback.parent.mkdir();library.rename(fallback);library.symlink_to(outside)
  source=self.root/'consumer.c'
  subprocess.run(['xcrun','clang','-arch','arm64',str(source),str(fallback),'-Wl,-rpath,@executable_path/../Frameworks','-Wl,-rpath,@executable_path/../Resources','-o',str(main)],check=True)
  with self.assertRaisesRegex(RuntimeError,'libfixture.dylib'):
   self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_empty_first_runpath_does_not_hide_valid_later_library(self):
  app,main,library=self.linked_fixture();source=self.root/'consumer.c'
  subprocess.run(['xcrun','clang','-arch','arm64',str(source),str(library),'-Wl,-rpath,@executable_path/../Empty','-Wl,-rpath,@executable_path/../Frameworks','-o',str(main)],check=True)
  self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_helper_executable_path_is_its_actual_directory(self):
  app,main,library=self.linked_fixture(location='Helpers/Libraries',runpath=None,install_name='@executable_path/Libraries/libfixture.dylib')
  helper=app/'Contents/Helpers/Worker';main.rename(helper)
  self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_unreferenced_library_has_no_guessed_executable_context(self):
  app,main,library=self.linked_fixture()
  source=self.root/'unused.c';source.write_text('int unused(void){return 0;}\n')
  unused=app/'Contents/Frameworks/libunused.dylib'
  subprocess.run(['xcrun','clang','-arch','arm64','-dynamiclib',str(source),'-Wl,-install_name,@rpath/libunused.dylib','-o',str(unused)],check=True)
  with self.assertRaisesRegex(RuntimeError,'libunused.dylib'):
   self.module.validate_dependencies(app,self.module.thin_bundle(app))
 def test_cyclic_library_dependencies_terminate(self):
  app,main,library=self.linked_fixture()
  parent=app/'Contents/Frameworks/libparent.dylib'
  source=self.root/'parent.c';source.write_text('extern int fixture(void);int parent(void){return fixture();}\n')
  subprocess.run(['xcrun','clang','-arch','arm64','-dynamiclib',str(source),str(library),'-Wl,-install_name,@rpath/libparent.dylib','-o',str(parent)],check=True)
  source=self.root/'library.c';source.write_text('extern int parent(void);int fixture(void){return parent();}\n')
  subprocess.run(['xcrun','clang','-arch','arm64','-dynamiclib',str(source),str(parent),'-Wl,-install_name,@rpath/libfixture.dylib','-o',str(library)],check=True)
  self.module.validate_dependencies(app,self.module.thin_bundle(app))
if __name__=='__main__':unittest.main()
