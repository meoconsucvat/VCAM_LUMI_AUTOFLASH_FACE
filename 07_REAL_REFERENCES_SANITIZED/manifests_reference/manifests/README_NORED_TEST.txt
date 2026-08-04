VCamPlus Kimiki package - metadata + relay contact + UI marker + no-red test

This package includes:
- Sileo metadata: VcamPlus
- Windows relay contact: @vcamplus
- iPhone UI marker: tele: @vcamplus
- Test patch to disable the red edge watermark text

Important:
- This is a TEST package until confirmed on a physical iPhone.
- Backend already accepts both signing markers:
  1) tele: @lumierephan
  2) tele: @vcamplus   
- VcamLumiereSensor.plist is preserved.
- Internal com.lumiere.* channels are not changed.

Test order:
1. Install DEB.
2. Open menu. If it resprings, uninstall and report immediately.
3. Login admin / 1234.
4. Confirm red edge text is gone after login.
5. Start relay + OBS.
6. Enable LIVE and confirm camera receives stream.
7. Leave it running for several minutes to check respring/safemode.
