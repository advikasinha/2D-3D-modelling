def import_cad_geometry(mapdl, file_path):
    """Import CAD geometry into MAPDL with geometry repair"""
    print(f"\nImporting CAD file...")
    print(f"File: {os.path.basename(file_path)}")
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.step', '.stp']:
            print("Format: STEP")
            
            # Upload file to MAPDL working directory
            print("Uploading file to ANSYS working directory...")
            mapdl.upload(file_path)
            
            # Get just the filename
            filename_only = os.path.basename(file_path)
            
            # Switch to AUX15 for import
            mapdl.aux15()
            
            # Set import options
            print("Configuring import options...")
            mapdl.ioptn('IGES', 'NO')
            mapdl.ioptn('MERGE', 'YES')
            mapdl.ioptn('SOLID', 'YES')
            mapdl.ioptn('SMALL', 'YES')
            mapdl.ioptn('GTOLER', 'DEFA')
            
            # Import STEP file using just the filename
            print(f"Reading STEP file: {filename_only}")
            try:
                mapdl.run(f"~PARAIN,'{filename_only}',STEP")
            except:
                # Try without tilde
                try:
                    mapdl.run(f"PARAIN,'{filename_only}',STEP")
                except:
                    # Try IGESIN method
                    file_no_ext = os.path.splitext(filename_only)[0]
                    mapdl.igesin(file_no_ext, 'STEP')
            
            # Switch to PREP7
            print("Switching to preprocessor...")
            mapdl.prep7()
            
            # CRITICAL: Check and repair geometry
            print("\nChecking imported geometry...")
            
            # Clean up geometry
            print("\n--- Initial Geometry Check ---")
            mapdl.nummrg('KP')  # Merge coincident keypoints
            # Note: NUMMRG only works with KP, NODE, ELEM, MAT, TYPE, REAL, CP, CE
            # Lines/Areas/Volumes don't need merging
            
            # Glue overlapping entities
            try:
                mapdl.vglue('ALL')  # Glue volumes
                mapdl.aglue('ALL')  # Glue areas
                mapdl.lglue('ALL')  # Glue lines
            except:
                pass  # Ignore if nothing to glue
            
            # Get counts
            num_kps = int(mapdl.get('_', 'KP', 0, 'COUNT'))
            num_lines = int(mapdl.get('_', 'LINE', 0, 'COUNT'))
            num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            
            print(f"Keypoints: {num_kps}")
            print(f"Lines: {num_lines}")
            print(f"Areas: {num_areas}")
            print(f"Volumes: {num_vols}")
            
            # If we have keypoints but no volumes, try to rebuild
            if num_kps > 0 and num_vols == 0:
                print("\n⚠ Geometry needs reconstruction...")
                print("Attempting to rebuild solid from surfaces...")
                
                # Try to create areas from lines if needed
                if num_areas == 0 and num_lines > 0:
                    print("Creating areas from lines...")
                    try:
                        mapdl.run('AL,ALL')  # Create area from all lines
                        num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
                        print(f"Areas created: {num_areas}")
                    except:
                        pass
                
                # Try to create volume from areas
                if num_areas > 0 and num_vols == 0:
                    print("Creating volume from areas...")
                    try:
                        # Select all areas
                        mapdl.allsel()
                        # Try to create volume
                        mapdl.run('VA,ALL')  # Create volume from all areas
                        num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                        print(f"Volumes created: {num_vols}")
                    except Exception as e:
                        print(f"Could not create volume: {e}")
                        
                        # Alternative: Try gluing areas together first
                        try:
                            print("Trying to glue areas...")
                            mapdl.aglue('ALL')
                            mapdl.run('VA,ALL')
                            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                            print(f"Volumes created: {num_vols}")
                        except:
                            pass
            
            # Final check
            num_kps = int(mapdl.get('_', 'KP', 0, 'COUNT'))
            num_lines = int(mapdl.get('_', 'LINE', 0, 'COUNT'))
            num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            
            print("\n" + "-"*60)
            print("FINAL GEOMETRY SUMMARY")
            print("-"*60)
            print(f"Keypoints: {num_kps}")
            print(f"Lines: {num_lines}")
            print(f"Areas: {num_areas}")
            print(f"Volumes: {num_vols}")
            
            if num_vols == 0 and num_areas == 0:
                print("\n✗ ERROR: No usable geometry!")
                print("\nThe STEP file imported but couldn't be converted to ANSYS geometry.")
                print("\nTROUBLESHOOTING OPTIONS:")
                print("1. Use 'cube' option to create geometry directly in ANSYS")
                print("2. Export from SolidWorks as IGES format instead")
                print("3. Simplify the geometry (remove small features)")
                print("4. Try Parasolid (.x_t) format if available")
                return False
            
            # Display geometry details
            if num_vols > 0:
                print("\n✓ 3D solid volumes found!")
                print("\nVolume list:")
                mapdl.vlist()
            elif num_areas > 0:
                print("\n✓ 2D surfaces found!")
                print("(Can mesh as shell elements)")
                print("\nArea list:")
                mapdl.alist()
            
            print("\n✓ Geometry ready for meshing!")
            return True
            
        elif ext in ['.iges', '.igs']:
            print("Format: IGES")
            
            # Upload file to MAPDL working directory
            print("Uploading file to ANSYS working directory...")
            mapdl.upload(file_path)
            
            # Get just the filename (no path, no extension)
            filename_only = os.path.basename(file_path)
            file_no_ext = os.path.splitext(filename_only)[0]
            
            print(f"Importing '{file_no_ext}' from ANSYS directory...")
            
            mapdl.aux15()
            mapdl.ioptn('MERGE', 'YES')
            mapdl.ioptn('SOLID', 'YES')
            mapdl.ioptn('SMALL', 'YES')
            
            # Now import using just the filename (no path)
            mapdl.igesin(file_no_ext)
            mapdl.prep7()
            
            # Apply same geometry checks
            print("\nCleaning up geometry...")
            mapdl.nummrg('KP')  # Only merge keypoints
            
            try:
                mapdl.vglue('ALL')
                mapdl.aglue('ALL')
                mapdl.lglue('ALL')
            except:
                pass
            
            num_kps = int(mapdl.get('_', 'KP', 0, 'COUNT'))
            num_lines = int(mapdl.get('_', 'LINE', 0, 'COUNT'))
            num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            
            print("\n" + "-"*60)
            print("GEOMETRY IMPORT SUMMARY")
            print("-"*60)
            print(f"Keypoints: {num_kps}")
            print(f"Lines: {num_lines}")
            print(f"Areas: {num_areas}")
            print(f"Volumes: {num_vols}")
            
            # Try to rebuild if needed
            if num_kps > 0 and num_vols == 0 and num_areas > 0:
                print("\nAttempting to create volume from areas...")
                try:
                    mapdl.allsel()
                    mapdl.run('VA,ALL')
                    num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                    print(f"Volumes created: {num_vols}")
                except:
                    pass
            
            if num_vols > 0 or num_areas > 0:
                print(f"\n✓ Imported successfully!")
                if num_vols > 0:
                    mapdl.vlist()
                elif num_areas > 0:
                    mapdl.alist()
                return True
            
            print("\n✗ No geometry found!")
            return False
            
        elif ext == '.sat':
            print("Format: SAT (ACIS)")
            mapdl.satin(file_path)
            mapdl.prep7()
            
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            return num_vols > 0
            
        elif ext == '.sldprt':
            print("\n" + "!"*60)
            print("! SolidWorks File Detected")
            print("!"*60)
            print("\nSolidWorks .sldprt files cannot be directly imported.")
            print("\nPlease export to STEP or IGES format first.")
            print("!"*60)
            return False
        
        return False
        
    except Exception as e:
        print(f"\n✗ ERROR importing geometry: {e}")
        print("\nFull error:")
        traceback.print_exc()
        return False