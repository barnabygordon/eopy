import numpy as np


def rper(image, inverse_dft=True):

    u = np.asarray(image, dtype=np.float64)
    m, n = u.shape

    arg = 2.*np.pi*np.fft.fftfreq(m, 1.)
    cos_m, sin_m = np.cos(arg), np.sin(arg)
    one_minus_exp_m = 1.0-cos_m-1j*sin_m

    arg = 2.*np.pi*np.fft.rfftfreq(n, 1.)
    cos_n, sin_n = np.cos(arg), np.sin(arg)
    one_minus_exp_n = 1.0-cos_n-1j*sin_n

    w1 = u[:, -1]-u[:, 0]
    w1_dft = np.fft.fft(w1)
    # Use complex fft because irfft2 needs all modes in the first direction
    v1_dft = w1_dft[:, None]*one_minus_exp_n[None, :]

    w2 = u[-1, :]-u[0, :]
    w2_dft = np.fft.rfft(w2)
    v2_dft = one_minus_exp_m[:, None]*w2_dft[None, :]

    k_dft = 2.0*(cos_m[:, None]+cos_n[None, :]-2.0)
    k_dft[0, 0] = 1.0
    s_dft = (v1_dft+v2_dft)/k_dft
    s_dft[0, 0] = 0.0

    if inverse_dft:
        s = np.fft.irfft2(s_dft, u.shape)
        return u-s, s
    else:
        u_dft = np.fft.rfft2(u)
        return u_dft-s_dft, s_dft
