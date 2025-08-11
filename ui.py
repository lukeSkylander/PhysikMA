import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import matplotlib
# Embed matplotlib using the TkAgg backend
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import animation
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import numpy as np


def main():
    root = tk.Tk()
    root.title("PhysikSim")

    dark_bg = "#000000"
    ax_bg = "#222222"
    fg_color = "#ffffff"
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=dark_bg)
    style.configure("TLabel", background=dark_bg, foreground=fg_color)
    style.configure("TLabelFrame", background=dark_bg, foreground=fg_color)
    style.configure("TCheckbutton", background=dark_bg, foreground=fg_color)
    style.configure("TButton", background="#444444", foreground=fg_color)
    style.configure(
        "TCombobox",
        fieldbackground="#444444",
        background=dark_bg,
        foreground=fg_color,
    )
    root.configure(bg=dark_bg)
    # Start with a reasonably large window so the animation and plots are
    # clearly visible.
    root.geometry("1920x1080")
    # 2x2 grid layout: left column for controls/description, right column for
    # animation and plots. Allocate more width to the right column so the
    # animation and graph have plenty of space.
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=99)
    # Give the animation (top-right) more vertical space than the plot below.
    # Increase the weight of the first row so the animation area expands
    # proportionally more compared to the plot underneath.
    root.rowconfigure(0, weight=3)
    root.rowconfigure(1, weight=1)

    # Automatically scale fonts with window size.
    default_fonts = [tkfont.nametofont(name)
                     for name in ("TkDefaultFont", "TkTextFont",
                                 "TkMenuFont", "TkHeadingFont")]
    slider_font = tkfont.Font(size=12)
    inputs = []
    desc_frame = None
    run_button = None
    MAX_BUTTON_WIDTH = 12
    last_font_size = None
    last_slider_font_size = None

    def resize_ui(event):
        """Adjust fonts when the window size changes."""
        nonlocal last_font_size, last_slider_font_size
        # Only handle resize events triggered by the root window itself
        if event.widget is not root:
            return
        size = max(8, int(min(event.width, event.height) / 50))
        ctrl_width = max(100, int(event.width * 0.35))

        if size != last_font_size:
            for f in default_fonts:
                f.configure(size=size)
            last_font_size = size

        entry_size = min(int(size * 1.4), 32)
        if entry_size != last_slider_font_size:
            slider_font.configure(size=entry_size)
            for e in inputs:
                e.configure(font=slider_font)
            last_slider_font_size = entry_size

        if desc_frame is not None:
            desc_frame.configure(width=ctrl_width)
        if run_button is not None:
            run_button.configure(width=min(MAX_BUTTON_WIDTH,
                                         max(1, ctrl_width // 30)))


    root.bind("<Configure>", resize_ui)

    options = ["RK4 Test 1", "RK4 Test 2", "RK4 Test 3", "Pendulum", "3D Pendulum"]
    option_var = tk.StringVar(value=options[0])

    # Frame for dropdown and input fields in the top-left quadrant
    control_frame = ttk.Frame(root)
    control_frame.grid(row=0, column=0, sticky="nsew")
    control_frame.columnconfigure(0, weight=0)
    control_frame.columnconfigure(1, weight=0)
    control_frame.columnconfigure(2, weight=0)

    dropdown = ttk.Combobox(control_frame, textvariable=option_var,
                            values=options, state="readonly")
    dropdown.grid(row=0, column=0, columnspan=3, padx=10, pady=10,
                  sticky="w")

    # Variables for pendulum parameters
    l_var = tk.DoubleVar(value=1.0)
    phi_var = tk.DoubleVar(value=np.degrees(0.1))  # polar angle
    psi_var = tk.DoubleVar(value=0.0)  # azimuth angle for 3D
    psi_dot_var = tk.DoubleVar(value=0.0)  # azimuth velocity for 3D
    g_var = tk.DoubleVar(value=9.81)
    h_var = tk.DoubleVar(value=0.01)
    drag_var = tk.DoubleVar(value=0.0)
    speed_var = tk.DoubleVar(value=1.0)
    show_forces_var = tk.BooleanVar(value=False)

    force_x_var = tk.DoubleVar(value=0.0)
    force_y_var = tk.DoubleVar(value=0.0)
    force_z_var = tk.DoubleVar(value=0.0)
    draw_mode_var = tk.BooleanVar(value=False)


    graph_options = ["Angle", "Angular velocity", "Angular acceleration", "Energy"]
    graph_var = tk.StringVar(value=graph_options[0])

    slider_frame = ttk.LabelFrame(control_frame, text="Pendulum Parameters")
    slider_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10,
                      sticky="nsew")
    slider_frame.columnconfigure(1, weight=1)

    def create_entry(var, row):
        entry = ttk.Entry(slider_frame, textvariable=var, font=slider_font)
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        inputs.append(entry)
        return entry

    ttk.Label(slider_frame, text="L", font=slider_font).grid(
        row=0, column=0, sticky="w", padx=5, pady=5)
    l_entry = create_entry(l_var, 0)

    ttk.Label(slider_frame, text="θ₀ (deg)", font=slider_font).grid(
        row=1, column=0, sticky="w", padx=5, pady=5)
    phi_entry = create_entry(phi_var, 1)

    psi_label = ttk.Label(slider_frame, text="ψ₀ (deg)", font=slider_font)
    psi_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
    psi_entry = create_entry(psi_var, 2)

    psi_dot_label = ttk.Label(
        slider_frame, text="ψ̇₀ (deg/s)", font=slider_font
    )
    psi_dot_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
    psi_dot_entry = create_entry(psi_dot_var, 3)

    ttk.Label(slider_frame, text="g", font=slider_font).grid(
        row=4, column=0, sticky="w", padx=5, pady=5)
    g_entry = create_entry(g_var, 4)

    ttk.Label(slider_frame, text="h", font=slider_font).grid(
        row=5, column=0, sticky="w", padx=5, pady=5)
    h_entry = create_entry(h_var, 5)

    ttk.Label(slider_frame, text="b", font=slider_font).grid(
        row=6, column=0, sticky="w", padx=5, pady=5)
    drag_entry = create_entry(drag_var, 6)

    ttk.Label(slider_frame, text="s", font=slider_font).grid(
        row=7, column=0, sticky="w", padx=5, pady=5)
    speed_entry = create_entry(speed_var, 7)

    force_x_label = ttk.Label(slider_frame, text="F_x", font=slider_font)
    force_x_label.grid(row=8, column=0, sticky="w", padx=5, pady=5)
    force_x_entry = create_entry(force_x_var, 8)

    force_y_label = ttk.Label(slider_frame, text="F_y", font=slider_font)
    force_y_label.grid(row=9, column=0, sticky="w", padx=5, pady=5)
    force_y_entry = create_entry(force_y_var, 9)

    force_z_label = ttk.Label(slider_frame, text="F_z", font=slider_font)
    force_z_label.grid(row=10, column=0, sticky="w", padx=5, pady=5)
    force_z_entry = create_entry(force_z_var, 10)


    draw_mode_check = ttk.Checkbutton(
        slider_frame,
        text="Draw trajectory",
        variable=draw_mode_var,
    )
    draw_mode_check.grid(row=11, column=0, columnspan=2, sticky="w", padx=5, pady=5)


    graph_dropdown = ttk.Combobox(control_frame, textvariable=graph_var,
                                  values=graph_options, state="readonly")
    graph_dropdown.grid(row=2, column=0, padx=10, pady=10, sticky="w")

    show_forces_check = ttk.Checkbutton(control_frame, text="Show forces",
                                        variable=show_forces_var)
    # Initially hidden; displayed conditionally in update_inputs

    # Bottom-left quadrant with a short description of the interface
    desc_frame = ttk.Frame(root)
    # Fill the lower left quadrant entirely so it doesn't overlap with the
    # input frame when the window is resized.
    desc_frame.grid(row=1, column=0, sticky="nsew")
    root.update_idletasks()
    desc_frame.configure(width=int(root.winfo_width() * 0.35))

    desc_text_default = (
        "Adjust parameters using the inputs above and press Run to start the "
        "simulation. The pendulum animation appears in the top-right quadrant "
        "while the chosen quantity is plotted below it."
    )
    desc_text_pend = (
        "L: pendulum length\n"
        "θ₀: initial polar angle (deg)\n"
        "g: gravitational acceleration\n"
        "h: time step\n"
        "b: air resistance coefficient\n"
        "s: animation speed"
    )
    desc_text_pend3d = (
        desc_text_pend + "\n"
        "ψ₀: initial azimuth angle (deg)\n"
        "ψ̇₀: initial azimuth angular velocity (deg/s)\n"
        "F_x, F_y, F_z: impulses along x, y, z"
    )

    desc_label = ttk.Label(desc_frame, text=desc_text_default, justify="left")
    # Keep the description left aligned without stretching across the column
    desc_label.pack(anchor="w", fill="x", padx=10, pady=10)

    def _resize_desc(event):
        desc_label.configure(wraplength=max(50, event.width - 20))

    desc_frame.bind("<Configure>", _resize_desc)

    def update_inputs(*args):
        """Enable or disable controls based on the selected module."""
        selection = option_var.get()
        pendulum_selected = selection in ("Pendulum", "3D Pendulum")

        if pendulum_selected:
            slider_frame.grid()
            state = tk.NORMAL
            if selection == "3D Pendulum":
                desc_label.configure(text=desc_text_pend3d)
            else:
                desc_label.configure(text=desc_text_pend)
        else:
            slider_frame.grid_remove()
            state = tk.DISABLED
            desc_label.configure(text=desc_text_default)

        for widget in slider_frame.winfo_children():
            widget.configure(state=state)

        if pendulum_selected:
            graph_dropdown.configure(state="readonly")
        else:
            graph_dropdown.configure(state=tk.DISABLED)

        if pendulum_selected:
            show_forces_check.grid(row=2, column=1, padx=10, pady=10, sticky="w")
            show_forces_check.configure(state=tk.NORMAL)
        else:
            show_forces_check.grid_remove()
            show_forces_check.configure(state=tk.DISABLED)
            show_forces_var.set(False)

        if selection == "3D Pendulum":
            psi_label.grid()
            psi_entry.grid()
            psi_dot_label.grid()
            psi_dot_entry.grid()
            force_x_label.grid()
            force_x_entry.grid()
            force_y_label.grid()
            force_y_entry.grid()
            force_z_label.grid()
            force_z_entry.grid()
            draw_mode_check.grid()
            draw_mode_check.configure(state=tk.NORMAL)
        else:
            psi_label.grid_remove()
            psi_entry.grid_remove()
            psi_dot_label.grid_remove()
            psi_dot_entry.grid_remove()
            force_x_label.grid_remove()
            force_x_entry.grid_remove()
            force_y_label.grid_remove()
            force_y_entry.grid_remove()
            force_z_label.grid_remove()
            force_z_entry.grid_remove()
            draw_mode_check.grid_remove()
            draw_mode_check.configure(state=tk.DISABLED)


    option_var.trace_add("write", update_inputs)
    update_inputs()

    def update_graph(*args):
        if option_var.get() in ("Pendulum", "3D Pendulum") and pendulum_data is not None:
            ax_plot.clear()
            ax_plot.set_facecolor(ax_bg)

            # Keep pendulum animation in ani[0] if available
            pend_anim = ani[0] if ani else None
            ani.clear()
            if pend_anim:
                ani.append(pend_anim)

            if graph_var.get() == "Energy":
                # Animate total, kinetic and potential energy together
                t = pendulum_data["t"]
                total = pendulum_data["Energy"]
                kinetic = pendulum_data["Kinetic"]
                potential = pendulum_data["Potential"]
                min_val = min(np.min(total), np.min(kinetic), np.min(potential))
                max_val = max(np.max(total), np.max(kinetic), np.max(potential))
                ani_line = animate_energy(fig_plot, ax_plot, t, kinetic,
                                          potential, total, speed_var.get(),
                                          (min_val, max_val))
            else:
                dataset = pendulum_data.get(graph_var.get(),
                                             pendulum_data["Angle"])
                ani_line = animate_line(fig_plot, ax_plot,
                                        pendulum_data["t"], dataset,
                                        speed_var.get())

            ani.append(ani_line)
            ax_plot.set_xlabel('t')
            ax_plot.set_ylabel(graph_var.get())
            canvas_plot.draw()

    graph_var.trace_add("write", update_graph)

    # Right side: top for animation, bottom for plot
    anim_frame = ttk.Frame(root)
    anim_frame.grid(row=0, column=1, sticky="nsew")
    plot_frame = ttk.Frame(root)
    plot_frame.grid(row=1, column=1, sticky="nsew")

    # Use a larger default figure size for better visibility and make sure the
    # canvas fills the available space in the frame.
    fig_anim, ax_anim = plt.subplots(figsize=(10, 8))
    fig_anim.patch.set_facecolor(dark_bg)
    ax_anim.set_facecolor(ax_bg)
    canvas_anim = FigureCanvasTkAgg(fig_anim, master=anim_frame)
    canvas_anim.get_tk_widget().pack(expand=True, fill="both", padx=5, pady=5)

    fig_plot, ax_plot = plt.subplots(figsize=(6, 5))
    fig_plot.patch.set_facecolor(dark_bg)
    ax_plot.set_facecolor(ax_bg)
    canvas_plot = FigureCanvasTkAgg(fig_plot, master=plot_frame)
    canvas_plot.get_tk_widget().pack(expand=True, fill="both", padx=10, pady=10)

    ani = []

    def animate_line(fig, ax, t, y, speed, y_range=None):
        """Animate a line plot on the given axes."""
        line, = ax.plot([], [], 'b-')
        ax.set_xlim(t[0], t[-1])
        if y_range is None:
            ax.set_ylim(min(y), max(y))
        else:
            ax.set_ylim(*y_range)
        ax.set_xlabel('t')
        ax.set_ylabel('y')
        ax.set_title('Animation')

        def init():
            line.set_data([], [])
            return line,

        def update(frame):
            line.set_data(t[:frame], y[:frame])
            return line,

        interval = max(1, int(30 / speed))
        return animation.FuncAnimation(fig, update, frames=len(t),
                                       init_func=init, blit=True,
                                       interval=interval, repeat=True)

    def animate_pendulum(fig, ax, t, phi, L, speed):
        ax.clear()
        x = L * np.sin(phi)
        y = -L * np.cos(phi)
        line, = ax.plot([], [], 'o-', lw=2, markersize=15)
        ax.set_xlim(-L * 1.2, L * 1.2)
        ax.set_ylim(-L * 1.2, L * 0.2)
        ax.set_aspect('equal', adjustable='box')
        ax.set_title('Pendulum')

        def init():
            line.set_data([], [])
            return line,

        def update(frame):
            line.set_data([0, x[frame]], [0, y[frame]])
            return line,

        interval = max(1, int(30 / speed))
        return animation.FuncAnimation(fig, update, frames=len(t),
                                       init_func=init, blit=True,
                                       interval=interval, repeat=True)

    def animate_pendulum3d(fig, ax, t, theta, psi, theta_dot, phi_dot,
                           L, g, speed,  draw_mode=False, show_forces=False,
                           applied_force=None):

        ax.clear()
        x = L * np.sin(theta) * np.cos(psi)
        y = L * np.sin(theta) * np.sin(psi)
        z = -L * np.cos(theta)
        line, = ax.plot([], [], [], 'o-', lw=2, markersize=8)
        arrows = []
        limit = L * 1.2
        ax.set_xlim(-limit, limit)
        ax.set_ylim(-limit, limit)
        ax.set_zlim(-limit, limit)
        ax.set_box_aspect([1, 1, 1])
        ax.set_title('3D Pendulum')
        line_xy, = ax.plot([], [], [], color="white", lw=1, alpha=0.5)
        line_yz, = ax.plot([], [], [], color="white", lw=1, alpha=0.5)
        line_zx, = ax.plot([], [], [], color="white", lw=1, alpha=0.5)

        def init():
            line.set_data([], [])
            line.set_3d_properties([])
            line_xy.set_data([], [])
            line_xy.set_3d_properties([])
            line_yz.set_data([], [])
            line_yz.set_3d_properties([])
            line_zx.set_data([], [])
            line_zx.set_3d_properties([])
            return line, line_xy, line_yz, line_zx

        def update(frame):
            line.set_data([0, x[frame]], [0, y[frame]])
            line.set_3d_properties([0, z[frame]])


            for arr in arrows:
                arr.remove()
            arrows.clear()

            if show_forces:
                # unit vector pointing from pivot to bob
                r_hat = np.array([
                    np.sin(theta[frame]) * np.cos(psi[frame]),
                    np.sin(theta[frame]) * np.sin(psi[frame]),
                    -np.cos(theta[frame])
                ])

                f_vec = None
                f_radial = 0.0
                if applied_force is not None:
                    f_vec = applied_force[frame]
                    f_radial = np.dot(f_vec, r_hat)

                # tension (mass = 1)
                T = g * np.cos(theta[frame]) + L * (
                    theta_dot[frame]**2 +
                    (np.sin(theta[frame])**2) * phi_dot[frame]**2
                ) - f_radial
                t_vec = -T * r_hat

                # gravity
                g_vec = np.array([0.0, 0.0, -g])

                # scale arrows by force magnitude
                force_scale = 0.3 * L / g if g != 0 else 0.3 * L

                arrows.append(ax.quiver(x[frame], y[frame], z[frame],
                                        g_vec[0], g_vec[1], g_vec[2],
                                        length=force_scale, normalize=False,
                                        color="blue"))
                arrows.append(ax.quiver(x[frame], y[frame], z[frame],
                                        t_vec[0], t_vec[1], t_vec[2],
                                        length=force_scale, normalize=False,
                                        color="red"))
                if f_vec is not None:
                    arrows.append(ax.quiver(x[frame], y[frame], z[frame],
                                            f_vec[0], f_vec[1], f_vec[2],
                                            length=force_scale, normalize=False,
                                            color="green"))

            if draw_mode:
                line_xy.set_data(x[:frame+1], y[:frame+1])
                line_xy.set_3d_properties(np.full(frame+1, -limit))
                line_yz.set_data(np.full(frame+1, limit), y[:frame+1])
                line_yz.set_3d_properties(z[:frame+1])
                line_zx.set_data(x[:frame+1], np.full(frame+1, -limit))
                line_zx.set_3d_properties(z[:frame+1])
                artists = [line, line_xy, line_yz, line_zx, *arrows]
            else:
                artists = [line, *arrows]

            return tuple(artists)


        interval = max(1, int(30 / speed))
        return animation.FuncAnimation(fig, update, frames=len(t),
                                       init_func=init, blit=False,
                                       interval=interval, repeat=True)

    def animate_energy(fig, ax, t, kinetic, potential, total, speed,
                       y_range=None):
        """Animate kinetic, potential and total energy lines together."""
        line_k, = ax.plot([], [], color="blue", label="Kinetic")
        line_p, = ax.plot([], [], color="red", label="Potential")
        line_t, = ax.plot([], [], color="white", label="Total")
        ax.set_xlim(t[0], t[-1])
        if y_range is None:
            y_min = min(np.min(kinetic), np.min(potential), np.min(total))
            y_max = max(np.max(kinetic), np.max(potential), np.max(total))
            ax.set_ylim(y_min, y_max)
        else:
            ax.set_ylim(*y_range)
        ax.set_xlabel('t')
        ax.set_ylabel('Energy')
        ax.set_title('Energy')
        ax.legend()

        def init():
            line_k.set_data([], [])
            line_p.set_data([], [])
            line_t.set_data([], [])
            return line_k, line_p, line_t

        def update(frame):
            line_k.set_data(t[:frame], kinetic[:frame])
            line_p.set_data(t[:frame], potential[:frame])
            line_t.set_data(t[:frame], total[:frame])
            return line_k, line_p, line_t

        interval = max(1, int(30 / speed))
        return animation.FuncAnimation(fig, update, frames=len(t),
                                       init_func=init, blit=True,
                                       interval=interval, repeat=True)

    pendulum_data = None

    def run_selected():
        nonlocal ani, pendulum_data, ax_anim
        selection = option_var.get()
        ax_plot.clear()
        ax_plot.set_facecolor(ax_bg)
        ax_anim.clear()
        ax_anim.set_facecolor(ax_bg)
        ani.clear()
        pendulum_data = None
        if selection == "RK4 Test 1":
            fig_anim.clf()
            fig_anim.patch.set_facecolor(dark_bg)
            ax_anim = fig_anim.add_subplot(111)
            ax_anim.set_facecolor(ax_bg)
            import rk4_test1 as mod
            t, y = mod.run(ax=ax_plot)
            ani.append(animate_line(fig_anim, ax_anim, t, y, speed_var.get()))
        elif selection == "RK4 Test 2":
            fig_anim.clf()
            fig_anim.patch.set_facecolor(dark_bg)
            ax_anim = fig_anim.add_subplot(111)
            ax_anim.set_facecolor(ax_bg)
            import rk4_test2 as mod
            t, y = mod.run(ax=ax_plot)
            ani.append(animate_line(fig_anim, ax_anim, t, y, speed_var.get()))
        elif selection == "RK4 Test 3":
            fig_anim.clf()
            fig_anim.patch.set_facecolor(dark_bg)
            ax_anim = fig_anim.add_subplot(111)
            ax_anim.set_facecolor(ax_bg)
            import rk4_test3 as mod
            t, x, _ = mod.run(ax=ax_plot)
            ani.append(animate_line(fig_anim, ax_anim, t, x, speed_var.get()))
        elif selection == "3D Pendulum":
            import pendulum3d as mod
            fig_anim.clf()
            fig_anim.patch.set_facecolor(dark_bg)
            ax_anim = fig_anim.add_subplot(111, projection="3d")
            ax_anim.set_facecolor(ax_bg)
            (t, theta, psi, theta_dot, phi_dot, energy) = mod.run(

                L=l_var.get(),
                theta0=np.radians(phi_var.get()),
                phi0=np.radians(psi_var.get()),
                phi_dot0=np.radians(psi_dot_var.get()),
                g=g_var.get(),
                h=h_var.get(),
                air_resistance=drag_var.get(),
                force_x=force_x_var.get(),
                force_y=force_y_var.get(),
                force_z=force_z_var.get(),
                plot=False,
            )

            L_val = l_var.get()
            g_val = g_var.get()
            drag_val = drag_var.get()
            kinetic = 0.5 * (L_val ** 2) * (
                theta_dot ** 2 + (np.sin(theta) ** 2) * phi_dot ** 2
            )
            potential = g_val * L_val * (1 - np.cos(theta))
            acceleration = (
                np.sin(theta) * np.cos(theta) * phi_dot ** 2
                - (g_val / L_val) * np.sin(theta)
                - drag_val * theta_dot * np.abs(theta_dot)
            )
            pendulum_data = {
                "t": t,
                "Angle": theta,
                "Angular velocity": theta_dot,
                "Angular acceleration": acceleration,
                "Energy": energy,
                "Kinetic": kinetic,
                "Potential": potential,
            }

            applied = None
            if show_forces_var.get() and (
                force_x_var.get() or force_y_var.get() or force_z_var.get()
            ):
                applied = np.tile(
                    [force_x_var.get(), force_y_var.get(), force_z_var.get()],
                    (len(t), 1),
                )

            ani.append(
                animate_pendulum3d(
                    fig_anim,
                    ax_anim,
                    t,
                    theta,
                    psi,
                    theta_dot,
                    phi_dot,
                    l_var.get(),
                    g_val,
                    speed_var.get(),
                    draw_mode_var.get(),
                    show_forces_var.get(),
                    applied,
                )
            )
            dataset = pendulum_data.get(graph_var.get(), pendulum_data["Angle"])
            if graph_var.get() == "Energy":
                min_val = min(np.min(dataset), np.min(kinetic), np.min(potential))
                max_val = max(np.max(dataset), np.max(kinetic), np.max(potential))
                ani.append(
                    animate_energy(
                        fig_plot,
                        ax_plot,
                        t,
                        kinetic,
                        potential,
                        dataset,
                        speed_var.get(),
                        (min_val, max_val),
                    )
                )
            else:
                ani.append(
                    animate_line(fig_plot, ax_plot, t, dataset, speed_var.get())
                )
            ax_plot.set_xlabel('t')
            ax_plot.set_ylabel(graph_var.get())
        else:  # Pendulum
            fig_anim.clf()
            fig_anim.patch.set_facecolor(dark_bg)
            ax_anim = fig_anim.add_subplot(111)
            ax_anim.set_facecolor(ax_bg)
            import pendulum as mod
            t, phi, omega, energy = mod.run(
                L=l_var.get(),
                phi0=np.radians(phi_var.get()),
                g=g_var.get(),
                h=h_var.get(),
                air_resistance=drag_var.get(),
                plot=False,
            )
            L_val = l_var.get()
            g_val = g_var.get()
            drag_val = drag_var.get()
            kinetic = 0.5 * (L_val ** 2) * omega ** 2
            potential = g_val * L_val * (1 - np.cos(phi))
            acceleration = (-(g_val / L_val) * np.sin(phi)
                            - drag_val * omega * np.abs(omega))
            pendulum_data = {
                "t": t,
                "Angle": phi,
                "Angular velocity": omega,
                "Angular acceleration": acceleration,
                "Energy": energy,
                "Kinetic": kinetic,
                "Potential": potential,
            }
            ani.append(animate_pendulum(fig_anim, ax_anim, t, phi, l_var.get(),
                                       speed_var.get()))
            dataset = pendulum_data.get(graph_var.get(), pendulum_data["Angle"])
            if graph_var.get() == "Energy":
                min_val = min(np.min(dataset), np.min(kinetic), np.min(potential))
                max_val = max(np.max(dataset), np.max(kinetic), np.max(potential))
                ani.append(animate_energy(fig_plot, ax_plot, t, kinetic, potential,
                                          dataset, speed_var.get(),
                                          (min_val, max_val)))
            else:
                ani.append(animate_line(fig_plot, ax_plot, t, dataset,
                                        speed_var.get()))
            ax_plot.set_xlabel('t')
            ax_plot.set_ylabel(graph_var.get())
        canvas_anim.draw()
        canvas_plot.draw()

    run_button = ttk.Button(control_frame, text="Run", command=run_selected)
    run_button.grid(row=2, column=2, padx=10, pady=10, sticky="w")
    run_button.configure(width=min(MAX_BUTTON_WIDTH,
                                   max(1, int(root.winfo_width() * 0.35) // 30)))

    root.mainloop()


if __name__ == "__main__":
    main()
