# import numpy as np
from manim import *
from CoolProp import CoolProp

# First define some important values for the plotting

# The minimum pressure used for generating the saturation curve is the atmospheric pressure
pmin = CoolProp.PropsSI('P', 'T', 100 + 273.15, 'Q', 0, 'Water')
# On the other hand, the maximum pressure is the critical pressure for water
pmax = CoolProp.PropsSI('Water', 'Pcrit')
# Also get the temperature for water at critical state
Tmax = CoolProp.PropsSI('Water', 'Tcrit')
# From the previously defined minimum pressure, get a minimum volume to plot the curve
vmin = 1 / (CoolProp.PropsSI('D', 'P', pmin, 'Q', 0, 'Water'))
# Use the minimum pressure to also get a maximum volume (notice I've divided the pressure by 5, so I can get a nice
# extension of the curve to the vapor side of the diagram)
vmax = 1 / (CoolProp.PropsSI('D', 'P', pmin / 5, 'Q', 1, 'Water'))
# It is also important to know the volume at the critical state, which is basically the volume at the top
# of the saturation curve which is going to be plotted
vcrit = 1 / (CoolProp.PropsSI('D', 'P', pmax, 'T', Tmax, 'Water'))


# Now some functions must be defined, which will be used to generate the saturation and isothermal curves in the video

# First a function that receives the volume as input and then returns the corresponding pressure in the saturation curve
def p_from_v(vinput):
    # It was necessary to add some clearance around the critical point, i.e., the top of the saturation curve. This
    # results in the curve getting a bit distorted around the critical point, but it was necessary since around
    # this point the CoolProp library presented some convergence problems.
    flat_tol_liq = 0.11
    flat_tol_vap = 0.00

    # Get the input
    v = vinput

    # Check wether its below, above or near the critical volume, then calculate pressure accordingly
    if v < (1 - flat_tol_liq) * vcrit:
        p = CoolProp.PropsSI('P', 'D', 1 / v, 'Q', 0, 'Water')
    elif v > (1 + flat_tol_vap) * vcrit:
        p = CoolProp.PropsSI('P', 'D', 1 / v, 'Q', 1, 'Water')
    elif (v >= (1 - flat_tol_liq) * vcrit) and (v <= (1 + flat_tol_vap) * vcrit):
        p = pmax

    return p


# This function gets a temperature and an adjusted volume, i.e., already submitted to the log transforms shown in the
# video. It returns the pressure on the isothermal curve corresponding to the specified temperature
def p_from_log10v_at_T(vinput, tinput):
    T = tinput
    v = 10 ** vinput * vmin
    p = CoolProp.PropsSI('P', 'D', 1 / v, 'T', T, 'Water')

    return p


# This function gets similar inputs as the p_from_log10v_at_T function, but it treats the fluid as an ideal gas, not as
# a real fluid
def p_from_log10v_at_T_IDEAL(vinput, tinput):
    T = tinput
    v = 10 ** vinput * vmin
    R = CoolProp.PropsSI('GAS_CONSTANT', 'Water') / CoolProp.PropsSI('MOLARMASS', 'Water')
    p = R * T / v

    return p


# Now it is possible to define the scene itself
class pvtvideo(MovingCameraScene):

    # Define the construct method, which builds and runs the scene. Inside it there are methods for each animation step
    def construct(self):

        # Plot graph axis
        self.show_axis()
        # Plot p-v graph in linear scale
        self.plot_pv_linear()
        # Then transform the linear plot by applying a logarithmic transformation to the x-axis
        self.x_axis_to_log()
        # Resulting x-axis is shifted to the left, must be shifted back
        self.x_axis_shift_back()
        # Plot isothermal curves for real fluid
        self.isothermal_curves()
        # Plot isothermal curve for ideal gas, at same temperature from last isothermal curve
        self.isothermal_curves_ideal()

    # Below are the methods for each animation step in the construct method

    # Creation of the pressure-volume axes
    def show_axis(self):

        # Define axes using previously calculated limits for volume and pressure
        ax = Axes(
            x_range=[vmin, vmax],
            y_range=[0, np.ceil(pmax / 5e6) * 5e6],  # Ceil maximum pressure to 25 MPa
            tips=False,
            axis_config={"include_numbers": False, "include_ticks": False}
        )

        # Get the axes labels and store
        self.xlabel = ax.get_x_axis_label("v").shift(0.5 * DOWN)  # Also shift x label a bit downwards
        self.ylabel = ax.get_y_axis_label("P").shift(0.5 * LEFT)  # Also shift y label a bit to the left

        # Also store current axes
        self.current_axes = ax

        # Create axes on screen
        self.play(Create(ax))
        self.play(Write(self.xlabel))
        self.play(Write(self.ylabel))
        self.wait()

    # Plotting the pressure-volume curve in linear x and y scales
    def plot_pv_linear(self):

        # The graph is split in two for better plotting.
        # The first part is for vmin < v < vcrit, a very narrow range of volumes where the pressure varies substantially
        # with small volume changes
        curve1 = self.current_axes.plot(lambda v: p_from_v(v), x_range=[vmin, vcrit, (vcrit - vmin) / 1000], color=BLUE)

        # The second part is for vcrit < v < vmax. In this region, the pressure behaves more smoothly
        curve2 = self.current_axes.plot(lambda v: p_from_v(v), x_range=[vcrit, vmax, (vmax - vcrit) / 1000], color=BLUE)

        # Join both graphs into a single vectorized mobject
        pvlinearcurve = VGroup(curve1, curve2)

        # Create the curve
        self.play(Create(pvlinearcurve))
        self.wait()

        # Store the curve for future usage
        self.pvlinearcurve = pvlinearcurve

        # Now show a moving dot, to illustrate how steep the curve is...
        # Save camera initial frame
        self.camera.frame.save_state()

        # Create moving dot object, then zoom in camera towards the dot
        moving_dot = Dot().move_to(curve1.points[0]).set_color(ORANGE)
        self.play(Create(moving_dot))  # dot_at_end_graph, dot_at_start_graph, moving_dot)
        self.play(self.camera.frame.animate.scale(0.5).move_to(moving_dot))

        # Define updater for dot movement
        def update_curve(mob):
            mob.move_to(moving_dot.get_center())

        # Program dot movement, with camera following its trajectory
        self.camera.frame.add_updater(update_curve)
        dotanimgroup = Succession(
            MoveAlongPath(moving_dot, curve1, rate_func=rate_functions.ease_in_sine, run_time=1.5),
            MoveAlongPath(moving_dot, curve2, rate_func=rate_functions.ease_out_sine, run_time=1.5))
        self.play(dotanimgroup)
        self.camera.frame.remove_updater(update_curve)

        # Play dot movement
        self.play(Restore(self.camera.frame),
                  Uncreate(moving_dot))  # ,Uncreate(dot_at_start_graph),Uncreate(dot_at_end_graph))
        self.wait()

    # Transform the x-axis from linear to log scale
    def x_axis_to_log(self):

        # Define a pointwise log transform
        def pointlogtranform(point):

            # Get the coordinates of the point in relation to the axis
            point = self.current_axes.point_to_coords(point)

            # Get point coordinates
            x = point[0]  # Get x coordinate of point
            y = point[1]  # Get y coordinate of point

            # If x coordinate is negative, do nothing, otherwise apply log function
            if point[0] <= 0:
                pass
            else:
                x = np.log10(x)

            # Convert back from coordinates to point, then return
            point = self.current_axes.coords_to_point(x, y)
            return point

        # Before transforming the curve, change the x-axis label
        xlabelnew = MathTex(r"\log_{10} \left(v\right)").move_to(self.xlabel)  # Create new label
        self.play(Unwrite(self.xlabel))  # Remove old label
        self.play(Write(xlabelnew))  # Show new label screen
        self.xlabel = xlabelnew  # Store new label
        self.wait()

        # Now apply the pointwise transformation to the curve previously generated
        self.play(ApplyPointwiseFunction(lambda point: pointlogtranform(point), self.pvlinearcurve))
        self.wait()

    # Shift x-axis to the right, to compensate leftward shift from previous transform
    def x_axis_shift_back(self):

        # Define a pointwise shift transform
        def pointshifttransform(point):
            # Get the coordinates of the point in relation to the axis
            point = self.current_axes.point_to_coords(point)

            # Get point coordinates
            x = point[0]  # Get x coordinate of point
            y = point[1]  # Get y coordinate of point

            x = x - np.log10(vmin)  # The shift to the right comes from subtracting the log of vmin

            # Convert back from coordinates to point, then return
            point = self.current_axes.coords_to_point(x, y)
            return point

        # Before transforming the curve, change the x-axis label once more
        xlabelnew = MathTex(r"\log_{10} \left(\frac{v}{v_0}\right)").move_to(self.xlabel)  # Create new label
        xlabelnew.shift(0.3 * LEFT + 0.1 * DOWN)  # Shift label a bit so it does not show over the x-axis
        self.play(Unwrite(self.xlabel))  # Remove old label
        self.play(Write(xlabelnew))  # Show new label on screen
        self.xlabel = xlabelnew  # Store new label
        self.wait()

        # Now apply the pointwise shift to the curve
        self.play(ApplyPointwiseFunction(lambda point: pointshifttransform(point), self.pvlinearcurve))
        self.wait()

    # Plot isothermal curves for real fluid
    def isothermal_curves(self):

        # First set the temperature which the isothermal is representing
        iso_temperature = 300 + 273.15
        # Store temperature for future usage
        self.iso_temperature = iso_temperature
        # Set a minimum volume for plotting the curve
        vminplot = 1 / (CoolProp.PropsSI('D', 'T', iso_temperature, 'P', pmax, 'Water'))
        # Also set the saturated liquid and saturated vapor volumes, i.e., the x-coordinates of the intersection
        # between isothermal curve and pressure-volume curve previously plotted
        v0 = 1 / (CoolProp.PropsSI('D', 'T', iso_temperature, 'Q', 0, 'Water'))
        v1 = 1 / (CoolProp.PropsSI('D', 'T', iso_temperature, 'Q', 1, 'Water'))
        # Also calculate saturation temperature, i.e., the y-coordinate of the intersection points
        psatT = CoolProp.PropsSI('P', 'T', iso_temperature, 'Q', 0, 'Water')

        # Now plot the isothermal. It has been split in three parts, for better plotting

        curve3 = self.current_axes.plot(lambda v: p_from_log10v_at_T(v, iso_temperature),
                                        x_range=[np.log10(vminplot) - np.log10(vmin), np.log10(v0) - np.log10(vmin)],
                                        color=RED)

        curve4 = self.current_axes.plot(lambda v: p_from_log10v_at_T(v, iso_temperature),
                                        x_range=[np.log10(v0) - np.log10(vmin), np.log10(v1) - np.log10(vmin)],
                                        color=RED)

        curve5 = self.current_axes.plot(lambda v: p_from_log10v_at_T(v, iso_temperature),
                                        x_range=[np.log10(v1) - np.log10(vmin), np.log10(vmax) - np.log10(vmin)],
                                        color=RED)

        # Join all curves into one single group
        tcurve = VGroup(curve3, curve4, curve5)

        # Also add an explanation text, to be shown before the isothermal curve is plotted
        explaintext = Tex("Let's say $T=cte$").move_to(2.5 * RIGHT + 3.3 * UP, LEFT)
        realgasequation = MathTex("P_{real} = P_{real}(v,T)", color=RED).move_to(2.5 * RIGHT + 1.8 * UP, LEFT)

        # Now show everything on screen

        # First the explaining text
        self.play(Write(explaintext))
        self.wait()

        # Now create the curve and corresponding explanation text
        self.play(Create(tcurve), Write(realgasequation))
        self.wait()

    # Plot isothermal curve for an ideal gas, at the same temperature of the previous curve
    def isothermal_curves_ideal(self):

        # Generate isothermal curve for ideal gas, starting with volume equal to the critical volume
        curve6 = self.current_axes.plot(lambda v: p_from_log10v_at_T_IDEAL(v, self.iso_temperature),
                                        x_range=[np.log10(vcrit) - np.log10(vmin), np.log10(vmax) - np.log10(vmin)],
                                        color=GREEN)

        # Also create an explanation text for the ideal gas curve
        idealgasequation = MathTex("P_{ideal} = \\frac{RT}{v}", color=GREEN).move_to(2.5 * RIGHT + 0.3 * UP, LEFT)

        # Now create both the curve and its explaning text
        self.play(Create(curve6), Write(idealgasequation))  # ,Write(tideallabel))
        self.wait(2)

        # Now the last explanation text
        limit_equation = MathTex("\lim_{P \\to 0 } \\frac{P_{ideal}}{P_{real}} = 1").move_to(2.5 * RIGHT + 1.2 * DOWN,
                                                                                             LEFT)
        self.play(Write(limit_equation))
        self.wait(5)
