// Independent development observer: raw OMETiffReader and real BF ImagePlus.
// Source-file launch intentionally compiles every owned statement before startup.
import ij.IJ;
import ij.ImagePlus;
import ij.CompositeImage;
import ij.measure.Calibration;
import java.lang.reflect.Array;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import loci.common.DebugTools;
import loci.common.services.ServiceFactory;
import loci.formats.FormatTools;
import loci.formats.in.OMETiffReader;
import loci.formats.meta.IMetadata;
import loci.formats.services.OMEXMLService;
import loci.plugins.BF;
import loci.plugins.in.ImporterOptions;
import ome.units.UNITS;
import ome.units.quantity.Length;

class ImagejExportReader {
  static Map<String, Object> map(Object... items) {
    Map<String, Object> result = new LinkedHashMap<>();
    for (int i = 0; i < items.length; i += 2) result.put((String) items[i], items[i + 1]);
    return result;
  }

  static String json(Object value) {
    if (value == null) return "null";
    if (value instanceof String) {
      String s = (String) value;
      StringBuilder out = new StringBuilder("\"");
      for (int i = 0; i < s.length(); i++) {
        char c = s.charAt(i);
        if (c == '"' || c == '\\') out.append('\\').append(c);
        else if (c < 32) out.append(String.format("\\u%04x", (int) c));
        else out.append(c);
      }
      return out.append('"').toString();
    }
    if (value instanceof Number || value instanceof Boolean) return value.toString();
    List<String> parts = new ArrayList<>();
    if (value instanceof Map<?, ?>) {
      for (Map.Entry<?, ?> entry : ((Map<?, ?>) value).entrySet())
        parts.add(json(entry.getKey().toString()) + ":" + json(entry.getValue()));
      return "{" + String.join(",", parts) + "}";
    }
    if (value instanceof Iterable<?>) {
      for (Object item : (Iterable<?>) value) parts.add(json(item));
    } else if (value.getClass().isArray()) {
      for (int i = 0; i < Array.getLength(value); i++) parts.add(json(Array.get(value, i)));
    } else throw new IllegalArgumentException("Unsupported owned JSON value type");
    return "[" + String.join(",", parts) + "]";
  }

  static Double micrometers(Length length) {
    return length == null ? null : length.value(UNITS.MICROMETER).doubleValue();
  }

  static ImporterOptions options() throws Exception {
    ImporterOptions o = new ImporterOptions();
    o.setLocation(ImporterOptions.LOCATION_LOCAL);
    o.setOpenAllSeries(true);
    o.setQuiet(true);
    o.setWindowless(true);
    o.setGroupFiles(false);
    o.setUngroupFiles(true);
    o.setMustGroup(false);
    o.setConcatenate(false);
    o.setSplitChannels(false);
    o.setSplitFocalPlanes(false);
    o.setSplitTimepoints(false);
    o.setCrop(false);
    o.setSpecifyRanges(false);
    o.setSwapDimensions(false);
    o.setAutoscale(false);
    o.setUpgradeCheck(false);
    o.setVirtual(false);
    o.setStitchTiles(false);
    o.setForceThumbnails(false);
    o.setShowMetadata(false);
    o.setShowOMEXML(false);
    o.setShowROIs(false);
    o.setUsingPatternIds(false);
    o.setColorMode(ImporterOptions.COLOR_MODE_GRAYSCALE);
    o.setStackFormat(ImporterOptions.VIEW_HYPERSTACK);
    o.setStackOrder(ImporterOptions.ORDER_XYCZT);
    return o;
  }

  static Map<String, Object> profile(ImporterOptions o) {
    return map("open_all_series", o.openAllSeries(), "quiet", o.isQuiet(),
      "windowless", o.isWindowless(), "group_files", o.isGroupFiles(),
      "ungroup_files", o.isUngroupFiles(), "must_group", o.doMustGroup(),
      "concatenate", o.isConcatenate(), "split_c", o.isSplitChannels(),
      "split_z", o.isSplitFocalPlanes(), "split_t", o.isSplitTimepoints(),
      "crop", o.doCrop(), "ranges", o.isSpecifyRanges(), "swap", o.isSwapDimensions(),
      "autoscale", o.isAutoscale(), "updater", o.doUpgradeCheck(),
      "virtual", o.isVirtual(), "stitch_tiles", o.doStitchTiles(),
      "force_thumbnails", o.isForceThumbnails(), "show_metadata", o.isShowMetadata(),
      "show_ome_xml", o.isShowOMEXML(), "show_rois", o.showROIs(),
      "pattern_ids", o.isUsingPatternIds(), "color_mode", o.getColorMode(),
      "stack_format", o.getStackFormat(), "stack_order", o.getStackOrder(),
      "location", o.getLocation(), "headless", System.getProperty("java.awt.headless"));
  }

  public static void main(String[] args) throws Exception {
    if (args.length < 2 || args.length > 3)
      throw new IllegalArgumentException("Expected input/startup, owned output and optional actual XML");
    DebugTools.setRootLevel("ERROR");
    ImporterOptions o = options();
    OMEXMLService service = new ServiceFactory().getInstance(OMEXMLService.class);
    IMetadata metadata = service.createOMEXMLMetadata();
    Map<String, Object> record = map("java_version", System.getProperty("java.version"),
      "java_vendor", System.getProperty("java.vendor"), "imagej_version", IJ.getVersion(),
      "java_runtime_version", System.getProperty("java.runtime.version"),
      "java_platform", map("os_name", System.getProperty("os.name"), "os_arch", System.getProperty("os.arch")),
      "bioformats_version", FormatTools.VERSION, "profile", profile(o),
      "startup_only", args[0].equals("--startup"));
    if (!args[0].equals("--startup")) {
      if (args.length != 3) throw new IllegalArgumentException("Actual carrier XML required");
      String carrierXML = Files.readString(Path.of(args[2]));
      record.put("carrier_ome_xml", carrierXML);
      record.put("carrier_schema_valid", service.validateOMEXML(carrierXML));
    }
    // Instantiation plus source launch is observer health, never a product verdict.
    try (OMETiffReader reader = new OMETiffReader()) {
      reader.setMetadataStore(metadata);
      reader.setGroupFiles(false);
      if (!args[0].equals("--startup")) {
        reader.setId(args[0]);
        List<Object> raw = new ArrayList<>();
        for (int s = 0; s < reader.getSeriesCount(); s++) {
          reader.setSeries(s);
          List<Object> planes = new ArrayList<>();
          for (int n = 0; n < reader.getImageCount(); n++) {
            int[] zct = reader.getZCTCoords(n);
            planes.add(map("n", n, "zct", zct,
              "bytes_base64", Base64.getEncoder().encodeToString(reader.openBytes(n))));
          }
          List<Object> channels = new ArrayList<>();
          for (int c = 0; c < metadata.getChannelCount(s); c++)
            channels.add(map("name", metadata.getChannelName(s, c),
              "samples_per_pixel", metadata.getChannelSamplesPerPixel(s, c).getValue()));
          raw.add(map("index", s, "name", metadata.getImageName(s),
            "dimensions_xyczt", new int[]{reader.getSizeX(), reader.getSizeY(), reader.getSizeC(), reader.getSizeZ(), reader.getSizeT()},
            "order", reader.getDimensionOrder(), "little_endian", reader.isLittleEndian(),
            "pixel_type", FormatTools.getPixelTypeString(reader.getPixelType()),
            "rgb", reader.isRGB(), "interleaved", reader.isInterleaved(),
            "resolution_count", reader.getResolutionCount(), "image_count", reader.getImageCount(),
            "physical_um", map("x", micrometers(metadata.getPixelsPhysicalSizeX(s)),
              "y", micrometers(metadata.getPixelsPhysicalSizeY(s)),
              "z", micrometers(metadata.getPixelsPhysicalSizeZ(s))),
            "channels", channels, "planes", planes));
        }
        record.put("raw_series", raw);
        record.put("raw_ome_xml", service.getOMEXML(metadata));
        List<String> used = new ArrayList<>();
        for (String file : reader.getUsedFiles()) used.add(Path.of(file).getFileName().toString());
        record.put("used_files", used);
      }
    }
    if (!args[0].equals("--startup")) {
      o.setId(args[0]);
      ImagePlus[] images = BF.openImagePlus(o);
      List<Object> observed = new ArrayList<>();
      try {
        for (ImagePlus image : images) {
          Calibration cal = image.getCalibration();
          List<Object> planes = new ArrayList<>();
          for (int t = 1; t <= image.getNFrames(); t++)
            for (int z = 1; z <= image.getNSlices(); z++)
              for (int c = 1; c <= image.getNChannels(); c++) {
                int stackIndex = image.getStackIndex(c, z, t);
                Object pixels = image.getStack().getPixels(stackIndex);
                long[] words = new long[Array.getLength(pixels)];
                String primitive;
                if (pixels instanceof short[]) {
                  primitive = "short[]";
                  short[] shorts = (short[]) pixels;
                  for (int i = 0; i < shorts.length; i++) words[i] = shorts[i] & 0xffff;
                } else if (pixels instanceof float[]) {
                  primitive = "float[]";
                  float[] floats = (float[]) pixels;
                  for (int i = 0; i < floats.length; i++)
                    words[i] = Integer.toUnsignedLong(Float.floatToRawIntBits(floats[i]));
                } else throw new IllegalStateException("Unexpected ImagePlus primitive type");
                planes.add(map("zct", new int[]{z - 1, c - 1, t - 1}, "stack_index", stackIndex,
                  "primitive", primitive, "words", words));
              }
          observed.add(map("title", image.getTitle(), "series_property", image.getProperty("Series"),
            "dimensions_xyczt", new int[]{image.getWidth(), image.getHeight(), image.getNChannels(), image.getNSlices(), image.getNFrames()},
            "bit_depth", image.getBitDepth(), "stack_size", image.getStackSize(),
            "open_as_hyperstack", image.getOpenAsHyperStack(),
            "composite_mode", image instanceof CompositeImage ? ((CompositeImage) image).getMode() : null,
            "calibration", map("x", cal.pixelWidth, "y", cal.pixelHeight, "z", cal.pixelDepth,
              "unit", cal.getUnit(), "x_unit", cal.getXUnit(), "y_unit", cal.getYUnit(), "z_unit", cal.getZUnit(),
              "frame_interval", cal.frameInterval, "time_unit", cal.getTimeUnit(),
              "origin", new double[]{cal.xOrigin, cal.yOrigin, cal.zOrigin},
              "value_unit", cal.getValueUnit(), "density_calibrated", cal.calibrated()),
            "ome_xml", image.getOriginalFileInfo().description, "planes", planes));
        }
      } finally {
        for (ImagePlus image : images) image.close();
      }
      record.put("imageplus", observed);
    }
    Files.writeString(Path.of(args[1]), json(record));
    System.out.println(args[0].equals("--startup") ? "OBSERVER_STARTUP_ONLY_OK" : "PRODUCT_OBSERVATION_RECORDED");
  }
}
