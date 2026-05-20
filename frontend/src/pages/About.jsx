import React from 'react'
import { ArrowRight, Check, Brain, Target, Leaf, Zap, Award, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

const About = () => {
  return (
    <main className="min-h-screen bg-stone-50/50 pt-16">
      {/* Hero Section */}
      <section className="relative px-6 py-20 lg:py-32 overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 right-10 w-72 h-72 bg-emerald-100/40 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 left-10 w-72 h-72 bg-amber-100/40 rounded-full blur-3xl"></div>
        </div>

        <div className="mx-auto max-w-5xl text-center space-y-6">
          <div className="inline-block">
            <span className="px-4 py-2 rounded-full bg-emerald-50 text-emerald-800 text-sm font-semibold border border-emerald-150">
              About AyurPulse
            </span>
          </div>

          <h1 className="text-5xl lg:text-6xl font-extrabold text-stone-900 tracking-tight text-balance">
            Your <span className="text-emerald-700">Natural Path</span> to Radiant Health
          </h1>

          <p className="text-xl max-w-2xl text-stone-600 mx-auto leading-relaxed">
            Discover the transformative power of Ayurvedic wellness combined with intelligent technology. We help you unlock your natural radiance from the inside out.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link
              to="/register"
              className="flex items-center justify-center gap-2 w-56 p-3.5 bg-emerald-700 text-white rounded-xl text-lg font-medium hover:bg-emerald-800 transition active:scale-95 shadow-lg shadow-emerald-700/10"
            >
              Start Your Journey <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="px-6 py-20 bg-gradient-to-br from-emerald-50/55 via-amber-50/20 to-transparent">
        <div className="mx-auto max-w-5xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <h2 className="text-4xl font-bold text-stone-900 tracking-tight">Our Mission</h2>
              <p className="text-lg text-stone-600 leading-relaxed">
                At AyurPulse, we believe that glowing skin and holistic wellness start with understanding yourself. Our mission is to bridge the gap between ancient Ayurvedic wisdom and modern innovation.
              </p>
              <p className="text-lg text-stone-600 leading-relaxed">
                We're on a mission to eliminate one-size-fits-all wellness solutions. Instead, we empower every user with personalized wellness strategies that align with their unique biological constitution, lifestyle, and goals.
              </p>
              <p className="text-lg text-stone-600 leading-relaxed">
                Whether you're struggling with acne, skin aging, or simply seeking radiant wellness, AyurPulse meets you where you are and guides you toward lasting, natural results.
              </p> 
              <Link
                to="/register"
                className="inline-flex items-center justify-center gap-2 w-52 p-3 bg-emerald-800 text-white rounded-xl text-lg font-medium hover:bg-emerald-900 transition active:scale-95 shadow-md shadow-emerald-900/10"
              >
                Explore AyurPulse <ArrowRight className="w-5 h-5" />
              </Link> 
            </div>

            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-100 to-amber-100 rounded-2xl blur-xl opacity-80"></div>
              <div className="relative bg-white border border-stone-200 rounded-2xl p-8 shadow-xl shadow-stone-200/50 space-y-6">
                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                    <Check className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-stone-850">Personalized Care</h4>
                    <p className="text-sm text-stone-500">Tailored to your unique constitution</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                    <Check className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-stone-850">AI-Powered Analysis</h4>
                    <p className="text-sm text-stone-500">Advanced skin condition detection technology</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                    <Check className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-stone-850">Natural Solutions</h4>
                    <p className="text-sm text-stone-500">Herbs, ingredients, and lifestyle swaps</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                    <Check className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-stone-850">Expert Doctor Vetting</h4>
                    <p className="text-sm text-stone-500">Qualified practitioners verifying and approving plans</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold text-stone-900 tracking-tight">Why Choose AyurPulse?</h2>
            <p className="text-lg max-w-2xl mx-auto text-stone-500 leading-relaxed">
              Experience the perfect blend of ancient Ayurvedic wisdom and modern artificial intelligence
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Box 1 */}
            <div className="group relative overflow-hidden rounded-xl border border-stone-200 p-8 bg-white hover:border-emerald-600 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="absolute inset-0 -z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br from-emerald-50/50 to-transparent"></div>
              <div className="mb-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-800">
                  <Brain className="w-6 h-6" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">Skin Recognition</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Upload face scans and get instant AI-powered analysis of underlying skin conditions such as acne, blackheads, pores, and wrinkles.
              </p>
            </div>

            {/* Box 2 */}
            <div className="group relative overflow-hidden rounded-xl border border-stone-200 p-8 bg-white hover:border-emerald-600 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="absolute inset-0 -z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br from-emerald-50/50 to-transparent"></div>
              <div className="mb-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-800">
                  <Target className="w-6 h-6" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">Dosha Calculation</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Take our quick-6 Prakriti assessment to determine your dominant Vata, Pitta, or Kapha constitution to customize dietary recommendations.
              </p>
            </div>

            {/* Box 3 */}
            <div className="group relative overflow-hidden rounded-xl border border-stone-200 p-8 bg-white hover:border-emerald-600 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="absolute inset-0 -z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br from-emerald-50/50 to-transparent"></div>
              <div className="mb-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-800">
                  <Leaf className="w-6 h-6" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">Dynamic Plan Assembly</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Receive personalized 7-day diet and lifestyle routines incorporating ingredient swaps dynamically tuned to your age, season, and habits.
              </p>
            </div>

            {/* Box 4 */}
            <div className="group relative overflow-hidden rounded-xl border border-stone-200 p-8 bg-white hover:border-emerald-600 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="absolute inset-0 -z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br from-emerald-50/50 to-transparent"></div>
              <div className="mb-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-800">
                  <Zap className="w-6 h-6" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">Wellness Routines</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Follow structured morning and evening skin routines, customized dietary directives, specific yoga practices, and wellness tips.
              </p>
            </div>

            {/* Box 5 */}
            <div className="group relative overflow-hidden rounded-xl border border-stone-200 p-8 bg-white hover:border-emerald-600 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="absolute inset-0 -z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br from-emerald-50/50 to-transparent"></div>
              <div className="mb-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-800">
                  <Award className="w-6 h-6" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">Vetted Dashboard</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Connect with registered Ayurvedic doctors who review, edit, and approve your plans for personalized safety.
              </p>
            </div>

            {/* Box 6 */}
            <div className="group relative overflow-hidden rounded-xl border border-stone-200 p-8 bg-white hover:border-emerald-600 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="absolute inset-0 -z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br from-emerald-50/50 to-transparent"></div>
              <div className="mb-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-800">
                  <Users className="w-6 h-6" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-stone-900 mb-2">OSM Shop Locator</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Geolocate nearby physical Ayurvedic ingredient stores and pharmacies using coordinates mapping for product sourcing.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Core Values Section */}
      <section className="px-6 py-20 bg-gradient-to-br from-transparent to-stone-100">
        <div className="mx-auto max-w-5xl">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold text-stone-900 tracking-tight">Our Core Values</h2>
            <p className="text-lg text-stone-500 max-w-2xl mx-auto leading-relaxed">
              Principles that guide everything we build and recommend
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="flex gap-4 p-6 rounded-xl border border-stone-200 bg-white shadow-sm hover:border-emerald-500 transition-all duration-200">
              <div className="shrink-0">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 text-emerald-800 flex items-center justify-center">
                  <Brain className="w-6 h-6" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-stone-900 mb-2">Empowerment Through Knowledge</h3>
                <p className="text-sm text-stone-600 leading-relaxed">
                  We empower individuals to take control of their skin wellness journey by providing education and tools grounded in ancient wisdom combined with modern science.
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-6 rounded-xl border border-stone-200 bg-white shadow-sm hover:border-emerald-500 transition-all duration-200">
              <div className="shrink-0">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 text-emerald-800 flex items-center justify-center">
                  <Leaf className="w-6 h-6" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-stone-900 mb-2">Sustainability & Nature</h3>
                <p className="text-sm text-stone-600 leading-relaxed">
                  Every recommendation prioritizes natural, sustainable solutions that work in harmony with your body, promoting clean living and environmental balance.
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-6 rounded-xl border border-stone-200 bg-white shadow-sm hover:border-emerald-500 transition-all duration-200">
              <div className="shrink-0">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 text-emerald-800 flex items-center justify-center">
                  <Users className="w-6 h-6" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-stone-900 mb-2">Community & Connection</h3>
                <p className="text-sm text-stone-600 leading-relaxed">
                  We believe wellness is a collaborative journey. Connecting users and verified health professionals helps establish credible, lasting care.
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-6 rounded-xl border border-stone-200 bg-white shadow-sm hover:border-emerald-500 transition-all duration-200">
              <div className="shrink-0">
                <div className="w-12 h-12 rounded-lg bg-emerald-50 text-emerald-800 flex items-center justify-center">
                  <Zap className="w-6 h-6" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-stone-900 mb-2">Continuous Innovation</h3>
                <p className="text-sm text-stone-600 leading-relaxed">
                  We combine cutting-edge technology with timeless Ayurvedic principles to constantly evolve and improve our analysis models.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-50 via-stone-50 to-amber-50/50 border border-stone-250 p-12 text-center shadow-lg">
            <div className="absolute inset-0 -z-10">
              <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-100 rounded-full blur-3xl opacity-50"></div>
            </div>
            <h2 className="text-3xl lg:text-4xl font-bold text-stone-900 mb-4">Ready to Discover Your Unique Wellness Blueprint?</h2>
            <p className="text-lg text-stone-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              Stop guessing what works for your skin. Start your personalized Ayurvedic wellness journey today and see results within weeks.
            </p>
            <div className="flex justify-center">
              <Link
                to="/register"
                className="flex items-center justify-center gap-2 w-52 p-3.5 bg-emerald-700 text-white rounded-xl text-lg font-medium hover:bg-emerald-800 transition active:scale-95 shadow-md shadow-emerald-700/10"
              >
                Get Started <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}

export default About
