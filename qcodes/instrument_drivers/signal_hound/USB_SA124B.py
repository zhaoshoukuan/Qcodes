from time import sleep, time
import numpy as np
import ctypes as ct
import logging

from qcodes.instrument.base import Instrument
from qcodes.utils import validators as vals


class SignalHound_USB_SA124B(Instrument):
    '''
    This is a direct port of the signal hound QTLab driver by Ramiro
    Status: Alpha version.
        This driver is functional but has untested features
        and is in need of a code cleanup.
    '''
    saStatus = {
        "saUnknownErr": -666,
        "saFrequencyRangeErr": -99,
        "saInvalidDetectorErr": -95,
        "saInvalidScaleErr": -94,
        "saBandwidthErr": -91,
        "saExternalReferenceNotFound": -89,
        # Device specific errors
        "saOvenColdErr": -20,
        # Data errors
        "saInternetErr": -12,
        "saUSBCommErr": -11,
        # General configuration errors
        "saTrackingGeneratorNotFound": -10,
        "saDeviceNotIdleErr": -9,
        "saDeviceNotFoundErr": -8,
        "saInvalidModeErr": -7,
        "saNotConfiguredErr": -6,
        "saDeviceNotConfiguredErr": -6,  # Added because key error raised
        "saTooManyDevicesErr": -5,
        "saInvalidParameterErr": -4,
        "saDeviceNotOpenErr": -3,
        "saInvalidDeviceErr": -2,
        "saNullPtrErr": -1,
        # No error
        "saNoError": 0,
        # Warnings
        "saNoCorrections": 1,
        "saCompressionWarning": 2,
        "saParameterClamped": 3,
        'saBandwidthClamped': 4
    }
    saStatus_inverted = {
        '-666': "saUnknownErr",
        '-99': "saFrequencyRangeErr",
        '-95': "saInvalidDetectorErr",
        '-94': "saInvalidScaleErr",
        '-91': "saBandwidthErr",
        '-89': "saExternalReferenceNotFound",
        '-20': "saOvenColdErr",
        '-12': "saInternetErr",
        '-11': "saUSBCommErr",
        '-10': "saTrackingGeneratorNotFound",
        '-9': "saDeviceNotIdleErr",
        '-8': "saDeviceNotFoundErr",
        '-7': "saInvalidModeErr",
        '-6': "saNotConfiguredErr",
        '-6': "saDeviceNotConfiguredErr",
        '-5': "saTooManyDevicesErr",
        '-4': "saInvalidParameterErr",
        '-3': "saDeviceNotOpenErr",
        '-2': "saInvalidDeviceErr",
        '-1': "saNullPtrErr",
        '0': "saNoError",
        '1': "saNoCorrections",
        '2': "saCompressionWarning",
        '3': "saParameterClamped",
        '4': 'saBandwidthClamped'
    }

    def __init__(self, name):
        t0 = time()
        self.log = logging.getLogger("Main.DeviceInt")
        logging.info(__name__ + ' : Initializing instrument SignalHound USB 124A')
        Instrument.__init__(self, name, tags=['physical'])
        self.dll = ct.CDLL("C:\Windows\System32\sa_api.dll")
        self.hf = constants()
        self.add_parameter('frequency',
                           label='Frequency ',
                           units='(GHz)',
                           get_cmd=self._do_get_frequency,
                           set_cmd=self._do_set_frequency,
                           parse_function=float)
        self.add_parameter('span',
                           label='Span ',
                           units='(GHz)',
                           get_cmd=self._do_get_span,
                           set_cmd=self._do_set_span,
                           parse_function=float)
        self.add_parameter('power',
                           label='Power ',
                           units='(dBm)',
                           get_cmd=self._do_get_power,
                           set_cmd=self._do_set_power,
                           vals=vals.Numbers(max_value=20),
                           parse_function=float)
        self.add_parameter('ref_lvl',
                           label='Reference power ',
                           units='(dBm)',
                           get_cmd=self._do_get_ref_lvl,
                           set_cmd=self._do_set_ref_lvl,
                           vals=vals.Numbers(max_value=20),
                           parse_function=float)
        self.add_parameter('external_reference',
                           get_cmd=self._do_get_external_reference,
                           set_cmd=self._do_set_external_reference,
                           vals=vals.Bool())
        self.add_parameter('device_type',
                           get_cmd=self._do_get_device_type,
                           set_cmd=self._do_set_device_type,
                           vals=vals.Anything())

        self.add_parameter('device_mode',
                           get_cmd=self._do_get_device_mode,
                           set_cmd=self._do_set_device_mode,
                           vals=vals.Anything())
        self.add_parameter('acquisition_mode',
                           get_cmd=self._do_get_acquisition_mode,
                           set_cmd=self._do_set_acquisition_mode,
                           vals=vals.Anything())

        self.add_parameter('scale',
                           get_cmd=self._do_get_scale,
                           set_cmd=self._do_set_scale,
                           vals=vals.Anything())
        self.add_parameter('running',
                           get_cmd=self._do_get_running,
                           set_cmd=self._do_set_running,
                           vals=vals.Bool())
        self.add_parameter('decimation',
                           get_cmd=self._do_get_decimation,
                           set_cmd=self._do_set_decimation,
                           vals=vals.Ints(1, 8))
        self.add_parameter('bandwidth',
                           label='Bandwidth',
                           units='(Hz)',
                           get_cmd=self._do_get_bandwidth,
                           set_cmd=self._do_set_bandwidth,
                           parse_function=float)
        # rbw Resolution bandwidth in Hz. RBW can be arbitrary.
        self.add_parameter('rbw',
                           label='Resolution Bandwidth',
                           units='(Hz)',
                           get_cmd=self._do_get_rbw,
                           set_cmd=self._do_set_rbw,
                           parse_function=float)
        # vbw Video bandwidth in Hz. VBW must be less than or equal to RBW.
        #  VBW can be arbitrary. For best performance use RBW as the VBW.
        self.add_parameter('vbw',
                           label='Video Bandwidth',
                           units='(Hz)',
                           get_cmd=self._do_get_vbw,
                           set_cmd=self._do_set_vbw,
                           parse_function=float)
        self.set('frequency', 5)
        self.set('span', .25e-3)
        self.set('power', 0)
        self.set('ref_lvl', 0)
        self.set('external_reference', False)
        self.set('device_type', 'Not loaded')
        self.set('device_mode', 'sweeping')
        self.set('acquisition_mode', 'average')
        self.set('scale', 'log-scale')
        self.set('running', False)
        self.set('decimation', 1)
        self.set('bandwidth', 0)
        self.set('rbw', 1e3)
        self.set('vbw', 1e3)
        self.openDevice()
        t1 = time()
        print('Initialized SignalHound in %.2fs' % (t1-t0))

    def openDevice(self):
        self.log.info("Opening Device")
        self.deviceHandle = ct.c_int(0)
        deviceHandlePnt = ct.pointer(self.deviceHandle)
        ret = self.dll.saOpenDevice(deviceHandlePnt)
        if ret != self.hf.saNoError:
            if ret == self.hf.saNullPtrErr:
                raise ValueError("Could not open device due to null-pointer error!")
            elif ret == self.hf.saDeviceNotOpenErr:
                raise ValueError("Could not open device!")
            else:
                raise ValueError("Could not open device due to unknown reason! Error = %d" % ret)

        self.devOpen = True
        self._devType = self.get('device_type')

    def closeDevice(self):
        self.log.info("Closing Device with handle num: ", self.deviceHandle.value)

        try:
            self.dll.saAbort(self.deviceHandle)
            self.log.info("Running acquistion aborted.")
        except Exception as e:
            self.log.info("Could not abort acquisition: %s", e)

        ret = self.dll.saCloseDevice(self.deviceHandle)
        if ret != self.hf.saNoError:
            raise ValueError("Error closing device!")
        print("Closed Device with handle num: ", self.deviceHandle.value)
        self.devOpen = False
        self._running = False

    def abort(self):
        self.log.info("Stopping acquisition")

        err = self.dll.saAbort(self.deviceHandle)
        if err == self.saStatus["saNoError"]:
            self.log.info("Call to abort succeeded.")
            self._running = False
        elif err == self.saStatus["saDeviceNotOpenErr"]:
            raise IOError("Device not open!")
        elif err == self.saStatus["saDeviceNotConfiguredErr"]:
            raise IOError("Device was already idle! Did you call abort without ever calling initiate()?")
        else:
            raise IOError("Unknown error setting abort! Error = %s" % err)

    def preset(self):
        self.log.warning("Performing hardware-reset of device!")
        self.log.warning("Please ensure you close the device handle within two seconds of this call!")

        err = self.dll.saPreset(self.deviceHandle)
        if err == self.saStatus["saNoError"]:
            self.log.info("Call to preset succeeded.")
        elif err == self.saStatus["saDeviceNotOpenErr"]:
            raise IOError("Device not open!")
        else:
            raise IOError("Unknown error calling preset! Error = %s" % err)



    def _do_get_frequency(self):
        return self._frequency

    def _do_set_frequency(self,freq):
        self._frequency = freq

    def _do_get_span(self):
        return self._span
    def _do_set_span(self,span):
        self._span = span

    def _do_get_power(self):
        return self._power
    def _do_set_power(self,power):
        self._power = power

    def _do_get_ref_lvl(self):
        return self._ref_lvl

    def _do_set_ref_lvl(self,ref_lvl):
        self._ref_lvl = ref_lvl

    def _do_get_external_reference(self):
        return self._external_reference

    def _do_set_external_reference(self, external_reference):
        self._external_reference = external_reference

    def _do_get_running(self):
        return self._running
    def _do_set_running(self, running):
        self._running = running

    def _do_get_device_type(self):
        self.log.info("Querying device for model information")

        devType = ct.c_uint(0)
        devTypePnt = ct.pointer(devType)

        err = self.dll.saGetDeviceType(self.deviceHandle, devTypePnt)
        if err == self.saStatus["saNoError"]:
            pass
        elif err == self.saStatus["saDeviceNotOpenErr"]:
            raise IOError("Device not open!")
        elif err == self.saStatus["saNullPtrErr"]:
            raise IOError("Null pointer error!")
        else:
            raise IOError("Unknown error setting getDeviceType! Error = %s" % err)

        if devType.value == self.hf.saDeviceTypeNone:
            dev = "No device"
        elif devType.value == self.hf.saDeviceTypeSA44:
            dev = "sa44"
        elif devType.value == self.hf.saDeviceTypeSA44B:
            dev = "sa44B"
        elif devType.value == self.hf.saDeviceTypeSA124A:
            dev = "sa124A"
        elif devType.value == self.hf.saDeviceTypeSA124B:
            dev = 'sa124B'
        else:
            raise ValueError("Unknown device type!")
        return dev

    def _do_set_device_type(self, device_type):
        self._device_type = device_type

    def _do_get_device_mode(self):
        return self._device_mode
    def _do_set_device_mode(self,device_mode):
        self._device_mode = device_mode
        return

    def _do_get_acquisition_mode(self):
        return self._acquisition_mode
    def _do_set_acquisition_mode(self,acquisition_mode):
        self._acquisition_mode = acquisition_mode
        return

    def _do_get_scale(self):
        return self._scale
    def _do_set_scale(self,scale):
        self._scale = scale

    def _do_get_decimation(self):
        return self.decimation
    def _do_set_decimation(self,decimation):
        self.decimation = decimation

    def _do_get_bandwidth(self):
        return self._bandwidth

    def _do_set_bandwidth(self, bandwidth):
        self._bandwidth = bandwidth

    def _do_get_rbw(self):
        return self._rbw

    def _do_set_rbw(self, rbw):
        self._rbw = rbw

    def _do_get_vbw(self):
        return self._vbw

    def _do_set_vbw(self, vbw):
        self._vbw = vbw


############################################################################

    def initialisation(self, flag=0):
        mode = self.get('device_mode')
        modeOpts = {
            "sweeping": self.hf.sa_SWEEPING,
            "real_time": self.hf.sa_REAL_TIME,
            "IQ": self.hf.sa_IQ,  # not implemented
            "idle": self.hf.sa_IDLE  # not implemented
        }
        if mode in modeOpts:
            mode = modeOpts[mode]
        else:
            raise ValueError("Mode must be one of %s. Passed value was %s." % (modeOpts, mode))
        err = self.dll.saInitiate(self.deviceHandle, mode, flag)

        ###################################
        # Below here only error handling
        ###################################
        if err == self.saStatus["saNoError"]:
            self._running = True
            self.log.info("Call to initiate succeeded.")
        elif err == self.saStatus["saDeviceNotOpenErr"]:
            raise IOError("Device not open!")
        elif err == self.saStatus["saInvalidParameterErr"]:
            print("saInvalidParameterErr!")
            print('In real-time mode, this value may be returned if the span',
                  'limits defined in the API header are broken. Also in',
                  'real-time mode, this error will be returned if the',
                  ' resolution bandwidth is outside the limits defined in',
                  ' the API header.')
            print('In time-gate analysis mode this error will be returned if',
                  ' span limits defined in the API header are broken. Also in',
                  ' time gate analysis, this error is returned if the',
                  ' bandwidth provided require more samples for processing',
                  ' than is allowed in the gate length. To fix this, ',
                  'increase rbw/vbw.')
            raise IOError("The value for mode did not match any known value.")
        # This error code does not exists!??
        # elif err == self.saStatus["saAllocationLimitError"]:
        #     print('This value is returned in extreme circumstances. The API',
        #           ' currently limits the amount of RAM usage to 1GB. When',
        #           ' exceptional parameters are provided, such as very low ',
        #           'bandwidths, or long sweep times, this error may be ',
        #           'returned. At this point you have reached the boundaries of',
        #           ' the device. The processing algorithms are optimized for',
        #           ' speed at the expense of space, which is the reason',
        #           ' this can occur.''')
        #     raise IOError("Could not allocate sufficent RAM!")
        elif err == self.saStatus["saBandwidthErr"]:
            raise IOError("RBW is larger than your span. (Sweep Mode)!")
        self.check_for_error(err)
        # else:
        #     raise IOError("Unknown error setting initiate! Error = %s" % err)

        return

    def QuerySweep(self):
        sweep_len = ct.c_int(0)
        start_freq = ct.c_double(0)
        stepsize = ct.c_double(0)
        err = self.dll.saQuerySweepInfo(self.deviceHandle, ct.pointer(sweep_len), ct.pointer(start_freq), ct.pointer(stepsize))
        if err == self.saStatus["saNoError"]:
            pass
        elif err == self.saStatus["saDeviceNotOpenErr"]:
            raise IOError("Device not open!")
        elif err == self.saStatus["saDeviceNotConfiguredErr"]:
            raise IOError("The device specified is not currently streaming!")
        elif err == self.saStatus["saNullPtrErr"]:
            raise IOError("Null pointer error!")
        else:
            raise IOError("Unknown error!")

        info = np.array([sweep_len.value, start_freq.value, stepsize.value])
        return info

    def configure(self, rejection=True):
        # CenterSpan Configuration
        frequency = self.get('frequency') * 1e9
        span = self.get('span') * 1e9
        center = ct.c_double(frequency)
        span = ct.c_double(span)
        self.log.info("Setting device CenterSpan configuration.")

        err = self.dll.saConfigCenterSpan(self.deviceHandle, center, span)
        self.check_for_error(err)

        # Acquisition configuration
        detectorVals = {
            "min-max": ct.c_uint(self.hf.sa_MIN_MAX),
            "average": ct.c_uint(self.hf.sa_AVERAGE)
        }
        scaleVals = {
            "log-scale": ct.c_uint(self.hf.sa_LOG_SCALE),
            "lin-scale": ct.c_uint(self.hf.sa_LIN_SCALE),
            "log-full-scale": ct.c_uint(self.hf.sa_LOG_FULL_SCALE),
            "lin-full-scale": ct.c_uint(self.hf.sa_LIN_FULL_SCALE)
        }
        if self._acquisition_mode in detectorVals:
            detector = detectorVals[self._acquisition_mode]
        else:
            raise ValueError("Invalid Detector mode! Detector  must be one of %s. Specified detector = %s" % (list(detectorVals.keys()), detector))
        if self._scale in scaleVals:
            scale = scaleVals[self._scale]
        else:
            raise ValueError("Invalid Scaling mode! Scaling mode must be one of %s. Specified scale = %s" % (list(scaleVals.keys()), scale))
        err = self.dll.saConfigAcquisition(self.deviceHandle, detector, scale)
        self.check_for_error(err)

        # Reference Level configuration
        ref = ct.c_double(self.get('ref_lvl'))
        # atten = ct.c_double(atten)
        self.log.info("Setting device reference level configuration.")
        err = self.dll.saConfigLevel(
            self.deviceHandle, ct.c_double(self.get('ref_lvl')))
        self.check_for_error(err)

        # External Reference configuration
        if self._external_reference:
            self.log.info("Setting reference frequency from external source.")
            err = self.dll.saEnableExternalReference(self.deviceHandle)
            self.check_for_error(err)

        if self._device_mode == 'sweeping':
            # Sweeping Configuration
            reject_var = ct.c_bool(rejection)
            self.log.info("Setting device Sweeping configuration.")
            err = self.dll.saConfigSweepCoupling(
                self.deviceHandle, ct.c_double(self.get('rbw')),
                ct.c_double(self.get('vbw')), reject_var)
            self.check_for_error(err)
        elif self._device_mode == 'IQ':
            err = self.dll.saConfigIQ(
                self.deviceHandle, ct.c_int(self.get('decimation')),
                ct.c_double(self.get('bandwidth')))
            self.check_for_error(err)
        return

    def sweep(self):
        # this needs an initialized device. Originally used by read_power()
        sweep_len = ct.c_int(0)
        start_freq = ct.c_double(0)
        stepsize = ct.c_double(0)
        err = self.dll.saQuerySweepInfo(self.deviceHandle,
                                        ct.pointer(sweep_len),
                                        ct.pointer(start_freq),
                                        ct.pointer(stepsize))
        if not err == self.saStatus['saNoError']:
            # if an error occurs tries preparing the device and then asks again
            print('Error raised in Sweep Info Query, preparing for measurement')
            sleep(.1)
            self.prepare_for_measurement()
            sleep(.1)
            err = self.dll.saQuerySweepInfo(self.deviceHandle,
                                            ct.pointer(sweep_len),
                                            ct.pointer(start_freq),
                                            ct.pointer(stepsize))
        self.check_for_error(err)
        end_freq = start_freq.value + stepsize.value*sweep_len.value
        freq_points = np.arange(start_freq.value*1e-9, end_freq*1e-9,
                                stepsize.value*1e-9)

        minarr = (ct.c_float * sweep_len.value)()
        maxarr = (ct.c_float * sweep_len.value)()
        sleep(.1)  # Added extra sleep for updating issue
        err = self.dll.saGetSweep_32f(self.deviceHandle, minarr, maxarr)
        sleep(.1)  # Added extra sleep
        if not err == self.saStatus['saNoError']:
            # if an error occurs tries preparing the device and then asks again
            print('Error raised in Sweep Info Query, preparing for measurement')
            sleep(.1)
            self.prepare_for_measurement()
            sleep(.1)
            minarr = (ct.c_float * sweep_len.value)()
            maxarr = (ct.c_float * sweep_len.value)()
            err = self.dll.saGetSweep_32f(self.deviceHandle, minarr, maxarr)

        if err == self.saStatus["saNoError"]:
            pass
        elif err == self.saStatus["saDeviceNotOpenErr"]:
            raise IOError("Device not open!")
        elif err == self.saStatus["saDeviceNotConfiguredErr"]:
            raise IOError("The device specified is not currently streaming!")
        elif err == self.saStatus["saNullPtrErr"]:
            raise IOError("Null pointer error!")
        elif err == self.saStatus["saInvalidModeErr"]:
            raise IOError("Invalid mode error!")
        elif err == self.saStatus["saCompressionWarning"]:
            raise IOError("Input voltage overload!")
        elif err == self.saStatus["sCUSBCommErr"]:
            raise IOError("Error ocurred in the USB connection!")
        else:
            raise IOError("Unknown error!")

        datamin = np.array([minarr[elem] for elem in range(sweep_len.value)])
        datamax = np.array([minarr[elem] for elem in range(sweep_len.value)])
        info = np.array([sweep_len.value, start_freq.value,
                        stepsize.value])

        return np.array([freq_points[0:sweep_len.value-1],
                        datamin, datamax, info])

    def get_power_at_freq(self, Navg=1):
        '''
        Returns the maximum power in a window of 250kHz
        around the specified  frequency.
        The integration window is specified by the VideoBandWidth (set by vbw)
        '''
        poweratfreq = 0
        for i in range(Navg):
            data = self.sweep()
            max_power = np.max(data[1][:])
            poweratfreq += max_power
        self._power = poweratfreq / Navg
        return self._power

    def get_spectrum(self, Navg=1):
        sweep_params = self.QuerySweep()
        data_spec = np.zeros(sweep_params[0])
        for i in range(Navg):
            data = self.sweep()
            data_spec[:] += data[1][:]
        data_spec[:] = data_spec[:] / Navg
        sweep_points = data[0][:]
        return np.array([data_spec, sweep_points])

    def prepare_for_measurement(self):
        self.set('device_mode', 'sweeping')
        self.configure()
        self.initialisation()
        return

    def safe_reload(self):
        self.closeDevice()
        self.reload()

    def check_for_error(self, err):
        if err != self.saStatus['saNoError']:
            err_msg = self.saStatus_inverted[str(err)]
            if err > 0:
                print('Warning:', err_msg)
            else:
                raise IOError(err_msg)

class constants():
    def __init__(self):
        self.SA_MAX_DEVICES = 8

        self.saDeviceTypeNone = 0
        self.saDeviceTypeSA44 = 1
        self.saDeviceTypeSA44B = 2
        self.saDeviceTypeSA124A = 3
        self.saDeviceTypeSA124B = 4

        self.sa44_MIN_FREQ = 1.0
        self.sa124_MIN_FREQ = 100.0e3
        self.sa44_MAX_FREQ = 4.4e9
        self.sa124_MAX_FREQ = 13.0e9
        self.sa_MIN_SPAN = 1.0
        self.sa_MAX_REF = 20
        self.sa_MAX_ATTEN = 3
        self.sa_MAX_GAIN = 2
        self.sa_MIN_RBW = 0.1
        self.sa_MAX_RBW = 6.0e6
        self.sa_MIN_RT_RBW = 100.0
        self.sa_MAX_RT_RBW = 10000.0
        self.sa_MIN_IQ_BANDWIDTH = 100.0
        self.sa_MAX_IQ_DECIMATION = 128

        self.sa_IQ_SAMPLE_RATE = 486111.111

        self.sa_IDLE      = -1
        self.sa_SWEEPING  = 0x0
        self.sa_REAL_TIME = 0x1
        self.sa_IQ        = 0x2
        self.sa_AUDIO     = 0x3
        self.sa_TG_SWEEP  = 0x4

        self.sa_MIN_MAX = 0x0
        self.sa_AVERAGE = 0x1

        self.sa_LOG_SCALE      = 0x0
        self.sa_LIN_SCALE      = 0x1
        self.sa_LOG_FULL_SCALE = 0x2
        self.sa_LIN_FULL_SCALE = 0x3

        self.sa_AUTO_ATTEN = -1
        self.sa_AUTO_GAIN  = -1

        self.sa_LOG_UNITS   = 0x0
        self.sa_VOLT_UNITS  = 0x1
        self.sa_POWER_UNITS = 0x2
        self.sa_BYPASS      = 0x3

        self.sa_AUDIO_AM  = 0x0
        self.sa_AUDIO_FM  = 0x1
        self.sa_AUDIO_USB = 0x2
        self.sa_AUDIO_LSB = 0x3
        self.sa_AUDIO_CW  = 0x4

        self.TG_THRU_0DB  = 0x1
        self.TG_THRU_20DB  = 0x2

        self.saUnknownErr = -666

        self.saFrequencyRangeErr = -99
        self.saInvalidDetectorErr = -95
        self.saInvalidScaleErr = -94
        self.saBandwidthErr = -91
        self.saExternalReferenceNotFound = -89

        self.saOvenColdErr = -20

        self.saInternetErr = -12
        self.saUSBCommErr = -11

        self.saTrackingGeneratorNotFound = -10
        self.saDeviceNotIdleErr = -9
        self.saDeviceNotFoundErr = -8
        self.saInvalidModeErr = -7
        self.saNotConfiguredErr = -6
        self.saTooManyDevicesErr = -5
        self.saInvalidParameterErr = -4
        self.saDeviceNotOpenErr = -3
        self.saInvalidDeviceErr = -2
        self.saNullPtrErr = -1

        self.saNoError = 0

        self.saNoCorrections = 1
        self.saCompressionWarning = 2
        self.saParameterClamped = 3
        self.saBandwidthClamped = 4